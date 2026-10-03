"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "../dsm_package/payload/ui/app.js"), "utf8");
const elements = new Map();
const requests = [];
let signature = 0;
const context = vm.createContext({
  document: {
    documentElement: {}, querySelectorAll: () => [],
    getElementById: (id) => {
      if (!elements.has(id)) elements.set(id, {addEventListener() {}});
      return elements.get(id);
    }
  },
  navigator: {language: "en"}, location: {origin: "https://nas.local:5001", protocol: "https:"},
  localStorage: {getItem: () => null},
  window: {parent: {synowebapi: {env: {
    getCredential: () => ({WaitForReady: async () => {}}),
    getRequestHeaders: () => ({"X-SYNO-TOKEN": "csrf", "X-SYNO-HASH": `proof.${++signature}`})
  }}}},
  fetch: async (url, options) => {
    requests.push({url, options});
    return {ok: true, status: 200, json: async () => (
      url.endsWith("action=pair") ? {pairing_code: "123456"} : {online: true, hostname: "NAS"}
    )};
  }
});

(async () => {
  vm.runInContext(source, context);
  await vm.runInContext("loadStatus()", context);
  await vm.runInContext("generateCode()", context);
  assert.equal(requests.length, 3);
  assert.equal(new Set(requests.map(r => r.options.headers["X-SYNO-HASH"])).size, 3);
  for (const {options} of requests) {
    assert.equal(options.headers["X-SYNO-TOKEN"], "csrf");
    assert.equal(options.credentials, "same-origin");
  }
  assert.equal(requests[2].options.headers["X-WakeLink-Action"], "pair");
  assert.equal(elements.get("pairing-code").textContent, "123456");
  context.window.parent = {SYNO: {SDS: {Session: {SynoToken: "legacy-csrf"}}}};
  assert.equal((await vm.runInContext("setupHeaders()", context))["X-SYNO-TOKEN"], "legacy-csrf");
  context.window.parent = context.window;
  assert.equal(Object.keys(await vm.runInContext("setupHeaders()", context)).length, 0);
  let powerSetups = 0;
  context.window.parent = {SYNO: {SDS: {WakeLink: {activeWindow: {
    authorizePowerPermission: async () => { powerSetups++; }
  }}}}};
  context.fetch = async () => ({ok: true, status: 200, json: async () => ({online: true, power_permission_enabled: true})});
  await vm.runInContext("authorizePower()", context);
  assert.equal(powerSetups, 1);
  assert.equal(elements.get("authorize-power").hidden, true);
  assert.equal(elements.get("power-status").textContent, "Permission enabled. No further setup needed.");
  context.window.parent = context.window;
  await vm.runInContext("authorizePower()", context);
  assert.equal(powerSetups, 1);
  assert.equal(elements.get("power-error").hidden, false);
  const classes = new Map();
  const mainContext = vm.createContext({
    Ext: {define: (name, cls) => classes.set(name, cls)},
    SYNO: {SDS: {Utils: {}}}, location: {protocol: "https:"}, setTimeout, clearTimeout
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../dsm_package/payload/ui/main.js"), "utf8"), mainContext);
  const authorize = classes.get("SYNO.SDS.WakeLink.MainWindow").authorizePowerPermission;
  async function runSetup({cancel = false, close = false, exitCode = 0, mismatch = false, failCreate = false, failDelete = false} = {}) {
    const calls = [];
    let created;
    mainContext.SYNO.SDS.Utils.PasswordConfirmDialog = class {
      constructor(options) { this.options = options; this.listeners = {}; }
      on(name, handler) { this.listeners[name] = handler; }
      open() {
        if (close) this.listeners.close();
        else if (cancel) this.options.cancelCallback();
        else this.options.callback({SynoConfirmPWToken: "temporary-test-token"});
      }
    };
    const owner = {sendWebAPI(request) {
      calls.push(request);
      if (request.method === "create") {
        created = request.params;
        request.callback(!failCreate, failCreate ? {code: 403} : {id: 42});
      } else if (request.method === "get") {
        request.callback(true, {name: mismatch ? "someone else's task" : created.name, owner: "root",
          enable: false, extra: created.extra});
      } else if (request.method === "get_history_status_list") {
        request.callback(true, [{stop_time: "complete", exit_code: exitCode}]);
      } else if (request.method === "delete") {
        request.callback(!failDelete, failDelete ? {code: 500} : {});
      } else { request.callback(true, {}); }
    }};
    let error;
    let result;
    try { result = await authorize.call(owner); } catch (caught) { error = caught; }
    assert.equal(owner.powerSetupBusy, false);
    return {calls, created, result, error};
  }
  const success = await runSetup();
  assert.equal(success.result, true);
  assert.deepEqual(success.calls.map(c => c.method), ["create", "get", "run", "get_history_status_list", "delete"]);
  assert.equal(success.created.enable, false);
  assert.equal(typeof success.created.schedule, "object");
  assert.equal(typeof success.created.extra, "object");
  assert.equal(success.created.schedule.repeat_date, 0);
  assert.equal(success.created.extra.script, "/usr/bin/python3 -I /var/packages/pcpowerfree/conf/power_permissions.py");
  for (const call of success.calls.filter(c => ["run", "delete"].includes(c.method))) {
    assert(Array.isArray(call.params.tasks));
    assert.equal(call.params.tasks.length, 1);
    assert.equal(call.params.tasks[0].id, 42);
    assert.equal(call.params.tasks[0].real_owner, "root");
  }
  assert.equal(success.created.SynoConfirmPWToken, "temporary-test-token");
  assert.equal(success.calls[0].api, "SYNO.Core.TaskScheduler.Root");
  assert.equal((await runSetup({cancel: true})).calls.length, 0);
  assert.equal((await runSetup({close: true})).calls.length, 0);
  const denied = await runSetup({failCreate: true});
  assert(denied.error);
  assert.deepEqual(denied.calls.map(c => c.method), ["create"]);
  for (const options of [{exitCode: 1}, {mismatch: true}, {failDelete: true}]) {
    const failure = await runSetup(options);
    assert(failure.error);
    assert.equal(failure.calls.at(-1).method, "delete");
    if (options.mismatch) assert(!failure.calls.some(c => c.method === "run"));
  }
  mainContext.location.protocol = "http:";
  await assert.rejects(() => authorize.call({}), /Secure DSM desktop required/);
  console.log("DSM desktop checks passed: signed sessions, pairing, limited power setup, cancellation and cleanup.");
})().catch(error => {console.error(error); process.exitCode = 1;});
