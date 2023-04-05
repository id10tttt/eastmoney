// pages/side-bar/side-bar.js
import stock_api from '../../api/stock.js'
import Toast from 'tdesign-miniprogram/toast/index'
Page({

  /**
   * 页面的初始数据
   */
  data: {
    stock_image: "/static/stock.png",
    display_stock_data: false,
    sideBarIndex: 0,
    scrollTop: 0,
    exchange_list: [],
    current_exchange: 'SSE',
    stock_data: [{
      exchange: '选项一',
      title: '标题一',
      badgeProps: {},
      items: [],
    }],
  },
  fetch_finance_stock_exchange(){
    let that = this
    let payload_data = {
      header: {

      },
      body: {

      }
    }
    stock_api.fetch_finance_exchange(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {
        that.setData({
          display_stock_data: true,
          exchange_list: result.data,
          current_exchange: result.data[0].title
        })
      } else {

      }
    })
  },
  fetch_finance_stock_list() {
    let that = this
    console.log(this.data)
    console.log(this.data.current_exchange)
    let payload_data = {
      header: {

      },
      body: {
        exchange: this.data.current_exchange
      }
    }
    stock_api.fetch_finance_stock(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {
        that.setData({
          display_stock_data: true,
          stock_data: result.data
        })
      } else {

      }
    })
  },
  onSideBarChange(e) {
    const {
      value
    } = e.detail;
    this.setData({
      sideBarIndex: value,
      current_exchange: this.data.exchange_list[value].title,
      stock_data: []
    });
    this.fetch_finance_stock_list()
  },
  redirectToStockDetailPage(stock_code) {
    var payload_data = {
      header: {

      },
      body: {
        stock_code: stock_code
      }
    }
    stock_api.validate_stock(payload_data).then(res => {
      var result = res.result;
      var code = result.code;
      if (code == 200) {
        var stock_data = {
          stock_code: stock_code
        }
        wx.navigateTo({
          url: '/pages/detail/detail?stock=' + JSON.stringify(stock_data),
        });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: result,
        });
      }
    })
  },
  onClickDisplayDetail(e) {
    let stock_code = e.currentTarget.dataset.value
    this.redirectToStockDetailPage(stock_code)
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {

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
    this.fetch_finance_stock_exchange()
    this.fetch_finance_stock_list()
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