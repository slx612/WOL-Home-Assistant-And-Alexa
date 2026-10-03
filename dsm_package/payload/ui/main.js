Ext.define("com.wakelink.Setup", {
  extend: "SYNO.SDS.AppInstance",
  appWindowName: "SYNO.SDS.WakeLink.MainWindow"
});

Ext.define("SYNO.SDS.WakeLink.MainWindow", {
  extend: "SYNO.SDS.AppWindow",

  constructor: function (options) {
    this.appInstance = options.appInstance;
    SYNO.SDS.WakeLink.MainWindow.superclass.constructor.call(this, Ext.apply({
      layout: "fit",
      resizable: true,
      maximizable: true,
      minimizable: true,
      showHelp: false,
      width: 800,
      height: 630,
      html: '<div style="height:100%"><iframe title="WakeLink" src="/webman/3rdparty/pcpowerfree/index.html?revision=@@DSM_PACKAGE_VERSION@@" style="width:100%;height:100%;border:0"></iframe></div>'
    }, options));
    SYNO.SDS.WakeLink.activeWindow = this;
  },

  authorizePowerPermission: async function () {
    if (location.protocol !== "https:" || this.powerSetupBusy) throw new Error("Secure DSM desktop required");
    this.powerSetupBusy = true;
    var taskId = null;
    var command = "/usr/bin/python3 -I /var/packages/pcpowerfree/conf/power_permissions.py";
    var taskName = "WakeLink power setup " + Date.now();
    var api = (name, method, version, params) => new Promise((resolve, reject) => {
      var timer = setTimeout(() => reject(new Error("DSM request timed out; check Task Scheduler before retrying")), 10000);
      this.sendWebAPI({api: name, method: method, version: version, params: params, scope: this,
        callback: function (success, data) {
          clearTimeout(timer);
          if (success) resolve(data);
          else {
            var error = new Error("DSM " + method + " failed");
            error.dsmCode = Number.isInteger(data?.code) ? data.code : "unknown";
            error.setupStage = method;
            reject(error);
          }
        }
      });
    });
    try {
      if (!SYNO.SDS.Utils.PasswordConfirmDialog) {
        await new Promise((resolve, reject) => {
          var script = document.createElement("script");
          script.src = "/webman/modules/Utils/PasswordConfirmDialog.js";
          script.onload = resolve;
          script.onerror = () => reject(new Error("DSM confirmation dialog unavailable"));
          document.head.appendChild(script);
        });
      }
      var confirmation = await new Promise((resolve) => {
        var dialog = new SYNO.SDS.Utils.PasswordConfirmDialog({
          module: this, owner: this, callback: resolve, cancelCallback: () => resolve(null), args: []
        });
        // DSM closes the dialog before delivering its confirmation token.
        dialog.on("close", () => setTimeout(() => resolve(null), 0));
        dialog.on("destroy", () => setTimeout(() => resolve(null), 0));
        dialog.open();
      });
      if (!confirmation?.SynoConfirmPWToken) return false;
      var created = await api("SYNO.Core.TaskScheduler.Root", "create", 4, {
        name: taskName, owner: "root", real_owner: "root", enable: false, type: "script",
        SynoConfirmPWToken: confirmation.SynoConfirmPWToken,
        // DSM's native client serializes nested objects; do not encode them twice.
        schedule: {date_type: 1, date: "2050/1/1", repeat_date: 0,
          hour: 0, minute: 0, repeat_hour: 0, repeat_min: 0, last_work_hour: 0, monthly_week: []},
        extra: {script: command, notify_enable: false, notify_if_error: false, notify_mail: ""}
      });
      confirmation = null;
      if (!Number.isSafeInteger(created?.id) || created.id < 0) throw new Error("Invalid DSM task ID");
      taskId = created.id;
      var task = await api("SYNO.Core.TaskScheduler", "get", 4, {id: taskId, real_owner: "root"});
      if (task.name !== taskName || task.owner !== "root" || task.enable !== false || task.extra?.script !== command) {
        var mismatch = new Error("DSM task did not match the limited setup");
        mismatch.setupStage = "verify";
        throw mismatch;
      }
      await api("SYNO.Core.TaskScheduler", "run", 2, {tasks: [{id: taskId, real_owner: "root"}]});
      for (var attempt = 0; attempt < 30; attempt++) {
        var history = await api("SYNO.Core.TaskScheduler", "get_history_status_list", 1, {id: taskId});
        if (Array.isArray(history) && history[0]?.stop_time) {
          if (history[0].exit_code !== 0) {
            var failure = new Error("DSM permission setup failed");
            failure.setupStage = "helper";
            failure.dsmCode = history[0].exit_code;
            throw failure;
          }
          return true;
        }
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      throw new Error("DSM setup timed out; refresh the permission status before retrying");
    } finally {
      try {
        if (taskId !== null) {
          await api("SYNO.Core.TaskScheduler", "delete", 2, {tasks: [{id: taskId, real_owner: "root"}]});
        }
      } finally {
        this.powerSetupBusy = false;
      }
    }
  },

  onClose: function () {
    if (SYNO.SDS.WakeLink.activeWindow === this) delete SYNO.SDS.WakeLink.activeWindow;
    SYNO.SDS.WakeLink.MainWindow.superclass.onClose.apply(this, arguments);
    this.doClose();
    return true;
  }
});
