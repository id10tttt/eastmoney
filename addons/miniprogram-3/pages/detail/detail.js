// pages/detail/detail.js
import stock_api from '../../api/stock.js'
import user_api from '../../api/user.js'
import Toast from 'tdesign-miniprogram/toast/index';

Page({

  /**
   * 页面的初始数据
   */
  data: {
    check_image: '/static/check.png',
    quota_image: '/static/quota.png',
    rain_image: '/static/rain.png',
    sun_image: '/static/sun.png',
    danger_image: '/static/danger.png',
    stock_code: '',
    token: '',
    user_code: '',
    free_data: {},
    visible_data: false,
    cur: {
      value: 'top',
      text: '更多指标包括：\n - 过去三年每股收益季度同比是否连续增长？\n- 资产投资回报环比是否保持增长？\n- 有在持续分红吗？\n- 销售情况是否健康？\n- 员工贡献度是否合理？\n- 经营现金流是否健康？\n- 等等......'
    }
  },

  // 添加自选
  addStore(e) {
    let code = e.currentTarget.dataset.value
    let payload_data = {
      "header": {},
      "body": {
        "stock_code": code
      }
    }
    user_api.add_collect(payload_data).then(res => {
      if (res.result.code = 200) {
        Toast({
          context: this,
          selector: '#t-toast',
          message: res.result.data,
          theme: 'warning',
          direction: 'column'
        });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: res.result.data,
          theme: 'warning',
          direction: 'column'
        });
      }
    })
  },
  //深度风险扫描
  addVip() {
    this.checkUserIsVIP();
  },
  goToSubscribe() {
    wx.navigateTo({
      url: '/pages/subscribe/subscribe',
    });
  },
  onVisibleChange(e) {
    this.setData({
      info_visible: e.detail.visible,
    });
  },
  showTips() {
    this.setData({
      info_visible: true
    });
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log(options.stock);
    let stock_data = JSON.parse(options.stock)
    this.setData({
      stock_code: stock_data.stock_code
    })
    this.getStockFreeData()
  },
  onClickUpdate() {
    this.getStockFreeData()
  },
  getStockFreeData() {
    let that = this
    let payload_data = {
      header: {},
      body: {
        stock_code: this.data.stock_code
      }
    }
    wx.showLoading({
      title: '加载中...',
    })
    stock_api.fetch_stock_free_value(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {
        that.setData({
          visible_data: true,
          free_data: {
            datas: result.data.data,
            stock_code: result.data.stock_code,
            stock_name: result.data.stock_name
          }
        })
        wx.hideLoading();
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: result.message,
          theme: 'warning',
          direction: 'column'
        });
        wx.hideLoading();
      }
    })
  },
  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {

  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    if (this.data.token) {
      console.log('let us dance!')
    } else {
      wx.login({
        timeout: 0,
        success(res) {
          wx.setStorageSync('token', useInfo.data.token)
          console.log('success res: ', res)
          this.setData({
            token: useInfo.data.token,
            user_code: res.code
          })
        },
        fail(res) {
          console.log('fail res: ', res)
        }
      })
    }
    if (this.data.stock_code && this.data.token) {
      var payload_data = {
        header: {

        },
        body: {
          stock_code: this.data.stock_code,
          token: this.data.token,
          user_code: this.data.user_code
        }
      }
      stock_api.list_mine_stock(payload_data).then(res => {
        console.log(res)
      })
    }
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

  },

  checkUserIsVIP() {
    let that = this
    wx.showLoading({
      title: '加载中...',
    })
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
          wx.hideLoading()
          let result = res.result
          let code = result.code
          if (code == 200) {
            var stock_data = {
              stock_code: that.data.stock_code
            }
            wx.navigateTo({
              url: '/pages/vip-detail/vip-detail?stock=' + JSON.stringify(stock_data),
            });
          } else if (code == 403) {
            wx.navigateTo({
              url: '/pages/subscribe/subscribe',
            });
          } else {
            Toast({
              context: this,
              selector: '#t-toast',
              message: result.data,
              theme: 'warning',
              direction: 'column'
            });
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
})