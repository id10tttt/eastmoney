import { post } from './utils/network.js'
App({
  globalData: {
    apiUrl: 'https://www.pickbest.cn',
    // apiUrl: 'http://127.0.0.1:8069',
    isIpx: false,
    aesKey: 'Hcl97tpCW3mc2Wd3'
  },
  onLaunch:function(){
if(!wx.getStorageSync('userToken')){
  wx.login({
    success: res => {
      // 发送 res.code 到后台换取 openId, sessionKey, unionId
      // 也就是发送到后端,后端通过接口发送到前端，前端接收用户信息等....
      wx.setStorageSync('code', res.code);
      let payload_data = {
        "body": {
         "code": res.code
        }
       }
      post(`${this.globalData.apiUrl}/api/wechat/mini/program/login`,payload_data).then(res => {
        if(res.result.code=200){
          wx.setStorageSync('openid', res.result.data.openid);
          wx.setStorageSync('userToken', res.result.data.token);
        }
      })
    }
  })

}
    

  },
  onShow:function(){
    
  },
   
    
});
