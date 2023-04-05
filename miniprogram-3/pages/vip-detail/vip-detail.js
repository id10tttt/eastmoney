// pages/vip-detail/vip-detail.js
import stock_api from '../../api/stock.js'
import Message from 'tdesign-miniprogram/message/index';
// const CryptoJS = require('../../utils/aes_util.js')

Page({

  /**
   * 页面的初始数据
   */
  data: {
    rain_image: '/static/rain.png',
    sun_image: '/static/sun.png',
    danger_image: '/static/danger.png',
    stock_code: '',
    stock_name: '',
    vip_content: [],
    default_content: 0,
    current_collapse: 0,
    benchmark_count: {}
  },
  syncVIPContent(type_id) {
    let that = this
    let payload_data = {
      header: {

      },
      body: {
        stock_code: this.data.stock_code,
        type_id: type_id
      }
    }
    stock_api.sync_stock_vip_content(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {

      } else {

      }
    })
  },
  handlehangeCollapse(e) {
    let current_collapse = e.detail.value
    if (current_collapse) {
      this.setData({
        current_collapse: current_collapse
      })
    }
    // this.syncVIPContent(current_collapse)
  },
  fetchStockVIPContetnt() {
    let that = this
    let payload_data = {
      header: {

      },
      body: {
        stock_code: this.data.stock_code
      }
    }
    wx.showLoading({
      title: '加载中...',
    })
    stock_api.fetch_stock_vip_content(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {
        wx.hideLoading({
          success: (res) => {},
        })

        // let data = result.data
        // console.log('decrypt_data: ', data.data, data.iv)
        // let descrypt_msg = CryptoJS.AesDecrypt(data.data)
        // console.log('descrypt_msg: ', descrypt_msg)
        // let decrypt_data = aes_decrypt_msg(data.data, data.iv)

        that.setData({
          vip_content: result.data.data,
          stock_code: result.data.stock_code,
          stock_name: result.data.stock_name,
          default_content: result.data.default_content,
          benchmark_count: result.data.benchmark_count
        })
      } else {
        wx.hideLoading({
          success: (res) => {},
        })
        Message.error({
          context: this,
          offset: [20, 32],
          duration: 5000,
          content: result.data,
        });
      }
    })
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    var stock_code = JSON.parse(options.stock)
    this.setData({
      stock_code: stock_code.stock_code
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
    this.fetchStockVIPContetnt()
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
  onShowDetailContent(e) {
    wx.showLoading({
      title: '加载中...',
    })
    let benchmark_id = e.target.dataset.value
    let that = this
    let payload_data = {
      header: {

      },
      body: {
        stock_code: this.data.stock_code,
        benchmark_id: benchmark_id
      }
    }
    stock_api.fetch_stock_vip_content_detail(payload_data).then(res => {
      wx.hideLoading()
      let result = res.result
      let code = result.code
      if (code == 200) {
        let res_data = result.data
        var benchmark_data = {
          stock_code: that.data.stock_code,
          benchmark_id: benchmark_id,
          data: res_data,
          benchmark: result.benchmark
        }
        wx.navigateTo({
          url: '/pages/vip-detail/content_detail/content_detail?benchmark_data=' + JSON.stringify(benchmark_data),
        });
      } else {
        Message.error({
          context: that,
          offset: [20, 32],
          duration: 5000,
          content: '暂无明细数据',
        });
      }
    })
  }
})