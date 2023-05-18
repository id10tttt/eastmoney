// pages/subscribe/subscribe.js
import subscribe_api from '../../api/subscribe.js'
import user_api from '../../api/user.js'
import Toast from 'tdesign-miniprogram/toast/index';

Page({

  /**
   * 页面的初始数据
   */
  data: {
    default_value: 0,
    subscrlbe_list: [{
      'name': '',
      'price_total': '',
      'uuid': '',
      'type': '',
      'duration_time': ''
    }],
    stock_code: ''
  },
  onChangeRadio(e) {
    this.setData({
      default_value: e.detail.value
    });
  },
  tapSubscribePay() {
    let choose_subscribe = this.data.subscrlbe_list[this.data.default_value]
    let price_total = choose_subscribe.price_total
    let subscribe_uuid = choose_subscribe.uuid
    let that = this
    wx.login({
      success: res => {
        let payload_data = {
          header: {
            code: res.code
          },
          body: {
            subscribe_uuid: subscribe_uuid,
            price: price_total
          }
        }
        subscribe_api.subscribe_item(payload_data).then(res => {
          console.log(res)
          let result = res.result
          let code = result.code
          if (code == 200) {
            wx.requestPayment({
              nonceStr: result.data.nonceStr,
              package: result.data.package,
              paySign: result.data.paySign,
              timeStamp: result.data.timeStamp,
              signType: result.data.signType,
              success(res) {
                wx.navigateBack()
                // wx.navigateTo({
                //   url: '/pages/vip-detail/vip-detail?stock=' + JSON.stringify({
                //     "stock_code": that.data.stock_code
                //   }),
                // });
              },
              fail(res) {
                Toast({
                  context: this,
                  selector: '#t-toast',
                  message: '支付失败',
                  theme: 'warning',
                  direction: 'column'
                });
              }
            })
          } else {
            Toast({
              context: this,
              selector: '#t-toast',
              message: result.message,
              theme: 'warning',
              direction: 'column'
            });
          }
        })
      }
    })
  },
  getSubscribeList() {
    let payload_data = {
      header: {

      },
      body: {

      }
    }
    subscribe_api.get_subscribe_list(payload_data).then(res => {
      let result = res.result
      let code = result.code
      let data = result.data
      if (code == 200) {
        this.setData({
          subscrlbe_list: data
        })
      }
    })
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    this.setData({
      stock_code: options.stock_code
    })
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {

  },

  chechUserSubscribe() {
    let that = this
    wx.getStorage({
      key: 'openid',
      success(res) {
        let open_id = res.data
        let payload_data = {
          header: {
            openid: open_id
          },
          body: {

          }
        }
        user_api.check_user_vip(payload_data).then(res => {
          let is_vip = res.result.data.vip
          if (is_vip) {
            wx.navigateBack({
              delta: 1,
            })
          }
        })
      },
      fail(res) {
        wx.navigateTo({
          url: '/pages/my/login/login',
        })
      }
    })
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    this.getSubscribeList();
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {

  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {

  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {

  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {

  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {

  }
})