const { CLOUD_ENV_ID } = require("./utils/cloud-config");

// app.js
App({
  onLaunch() {
    console.log("周易起卦小程序启动");

    if (!wx.cloud) {
      console.error("当前基础库不支持云能力");
      return;
    }

    wx.cloud.init({
      env: CLOUD_ENV_ID,
      traceUser: true,
    });
  },

  onShow() {
    // 小程序显示时
  },

  onHide() {
    // 小程序隐藏时
  },

  globalData: {
  },
});
