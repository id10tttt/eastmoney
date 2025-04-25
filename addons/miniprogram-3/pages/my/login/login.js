//获取应用实例
var app = getApp()
import login_api from '../../../api/login.js'
import Toast from 'tdesign-miniprogram/toast/index';
import Message from 'tdesign-miniprogram/message/index'

Page({
  data: {
    canIUse: wx.canIUse('button.open-type.getUserInfo'),
    isauthorize: false,
    sessionKey: '',
    hasSessionKey: false,
    userInfo: {},
    user_name: '',
    password: '',
    stock_code: ''
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad: function (options) {
    if(options.stock != 'undefined'){
      var stock_data =JSON.parse(options.stock)
      this.setData({
        stock_code: stock_data.stock_code
      })
    }
    let that = this
    wx.getSetting({
      success(res) {
        if (!res.authSetting['scope.userInfo'] || true) {
          wx.getUserInfo({
            success: function (res) {
              that.setData({
                userInfo: res.userInfo
              })
            }
          })
        }
      }
    })

  },
  get_user_login(code) {
    let that = this
    wx.showLoading({
      title: '加载中',
    })
    login_api.login_user({
      header: {

      },
      body: {
        code: code,
        user_info: that.data.userInfo
      }
    }).then(res => {
      var result = res.result
      var code = result.code
      var data = result.data
      if (code == 200) {
        wx.hideLoading({
          success: (res) => {},
        })
        that.setData({
          sessionKey: data.session_key,
          hasSessionKey: true,
          isauthorize: true
        })
        wx.setStorage({
          data: data.session_key,
          key: 'SESSIONKEY',
        })
        wx.setStorage({
          data: data.openid,
          key: 'openid',
        })

        // 小程序需要认证才能获取手机号码...
        that.settoken(result.data.token)
        that.set_userinfo(data.user_info)
        
      } else {
        Message.error({
          context: this,
          offset: [20, 32],
          duration: 5000,
          content: data,
        });
      }
    })
  },
  getPhoneNumber(e) {
    console.log('e: ', e)
    let that = this;
    let openid = wx.getStorageSync('openid')
    let payload_data = {
      header: {

      },
      body: {
        session_key: that.data.sessionKey,
        iv: e.detail.iv,
        encryptedData: e.detail.encryptedData,
        openid: openid,
        user_info: this.data.userInfo
      }
    }

    login_api.bind_user(payload_data).then(res => {
      let result = res.result
      console.log('bind_user result: ', result)
      let code = result.code
      let data = result.data
      if (code == 200) {
        this.settoken(data.token)
        this.set_userinfo(data.user_info)
      } else {
        Toast({
          context: that,
          selector: '#t-toast',
          message: result.data,
          theme: 'warning',
          direction: 'column'
        });
      }

    })
  },
  apiWxaUserLogin(){
    wx.login({
      success: res => {
        this.get_user_login(res.code) // 发送 res.code 到后台换取 openId, sessionKey, unionId
      }
    })
    // let that = this
    // //sessionKey 未过期，并且在本生命周期一直有效
    // let value = wx.getStorageSync('SESSIONKEY')
    // if (value) {
    //   that.setData({
    //     sessionKey: value,
    //     hasSessionKey: true
    //   })
    // } else {
    //   if (that.data.sessionKey == '') {
    //     wx.login({
    //       success: res => {
    //         that.get_user_login(res.code) // 发送 res.code 到后台换取 openId, sessionKey, unionId
    //       }
    //     })
    //   }
    // }
  },
  onShow: function () {
    wx.showLoading({
      title: '加载中',
    })
    setTimeout(function () {
      wx.hideLoading()
    }, 1000)
    let that = this
    wx.checkSession({
      success(res) {
        //sessionKey 未过期，并且在本生命周期一直有效
        let value = wx.getStorageSync('SESSIONKEY')
        if (value) {
          that.setData({
            sessionKey: value,
            hasSessionKey: true
          })
          var stock_data = {
            stock_code: that.data.stock_code
          }
          wx.reLaunch({
            url: '/pages/index/index?stock=' + JSON.stringify(stock_data),
          })
        } else {
          if (that.data.sessionKey == '') {
            wx.login({
              success: res => {
                that.get_user_login(res.code) // 发送 res.code 到后台换取 openId, sessionKey, unionId
              }
            })
          }
        }
      },
      fail() {
        // session_key 已经失效，需要重新执行登录流程
        wx.login({
          success: res => {
            that.get_user_login(res.code) // 发送 res.code 到后台换取 openId, sessionKey, unionId
          }
        })
      }
    })

  },
  settoken(data) {
    wx.setStorage({
      key: "userToken",
      data: {
        access_token: data.access_token,
      }
    })
    wx.setStorage({
      key: "refresh_userToken",
      data: {
        refresh_token: data.refresh_token
      }
    })
  },
  set_userinfo(data) {
    let that = this
    wx.setStorage({
      key: "userInfo",
      data: data
    })
    wx.showLoading({
      title: '加载中',
    })
    // wx.switchTab({
    //   url: '/pages/index/index'
    // })
    var stock_data = {
      stock_code: that.data.stock_code
    }
    wx.reLaunch({
      url: '/pages/index/index?stock=' + JSON.stringify(stock_data),
    })
  },
  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload: function () {

  },
  onChangeUserName(e) {
    this.setData({
      user_name: e.detail.value
    })
  },
  onChangePassword(e) {
    this.setData({
      password: e.detail.value
    })
  },
  onTapLogin() {
    let that = this
    if(this.data.user_name && this.data.password){
      let payload_data = {
        header: {

        },
        body: {
          user_name: this.data.user_name,
          password: this.data.password
        }
      }
      login_api.api_login(payload_data).then(res=>{
        let result = res.result
        let code = result.code
        if(code == 200){
          this.apiWxaUserLogin()
          wx.setStorage({
            key: 'api_uid',
            data: result.data.uid
          })
          var stock_data = {
            stock_code: that.data.stock_code
          }
          wx.reLaunch({
            url: '/pages/index/index?stock=' + JSON.stringify(stock_data),
          })
        }
        else{
          Toast({
            context: this,
            selector: '#t-toast',
            message: result.data,
            theme: 'warning',
            direction: 'column'
          });
        }
      })
    }
    else{
      Toast({
        context: this,
        selector: '#t-toast',
        message: '请输入用户名和密码',
        theme: 'warning',
        direction: 'column'
      });
    }
  },
})
