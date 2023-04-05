// index.js
import Toast from 'tdesign-miniprogram/toast/index';
import stock_api from '../../api/stock.js'
import login_api from '../../api/login.js'
import query_api from '../../api/query_his'

const app = getApp()

Page({

  
  /**
   * 页面的初始数据
   */
  data: {
    query_his: [],
    stock_code: ''
  },
  fetch_finance_stock_list(){
    let that = this
    let payload_data = {
      header: {

      },
      body: {

      }
    }
    stock_api.fetch_finance_stock(payload_data).then(res=>{
      let result = res.result
      let code = result.code
      if(code == 200){

      }else{
        
      }
    })
  },
  checkUserTokenValidate() {
    let that = this
    let payload_data = {
      header: {

      },
      body: {

      }
    }
    login_api.check_token(payload_data).then(res => {
      let result = res.result
      let code = result.code
      if (code == 200) {

      } 
      else {
        try {
          wx.removeStorageSync('SESSIONKEY')
          wx.removeStorageSync('userToken')
          wx.removeStorageSync('userInfo')
        } catch (e) {
          console.log('error: ', e)
          // Do something when catch error
        }
        // 如果没有登录，跳转至登录页面
        let stock_data = {
          stock_code: that.data.stock_code
        }
        
        console.log('stock_data: ', stock_data)
        wx.navigateTo({
          url: '/pages/my/login/login?stock=' + JSON.stringify(stock_data),
        })
      }
    })
  },
  onSideBarChange(e) {
    const { value } = e.detail;

    this.setData({ sideBarIndex: value });
  },
  onClickDisplayDetail(e){
    console.log(e)
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    if(options.stock != 'undefined' && options.stock){
      var stock_data =JSON.parse(options.stock)
      this.setData({
        stock_code: stock_data.stock_code
      })
      this.onClickSearch()
    }
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {

  },

  fetchQueryHis(){
    let that = this
    let payload_data = {
      header: {

      },
      body: {

      }
    }
    query_api.query_his(payload_data).then(res=>{
      let result = res.result
      let code = result.code
      if(code == 200){
        that.setData({
          query_his: result.data.data
        })
      }
    })
  },
  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    this.fetchQueryHis()
  },
  handleCloseTag(e){
    let stock_code = e.target.dataset.value
    let that = this
    let payload_data = {
      header: {

      },
      body: {
        key: stock_code
      }
    }
    query_api.unlink_query_his(payload_data).then(res=>{
      let result = res.result
      let code = result.code
      if(code == 200){
        that.fetchQueryHis()
      }
    })
  },
  onClickOpenPage(e){
    let stock_code = e.target.dataset.value
    this.setData({
      stock_code: stock_code
    })
    this.onClickSearch()
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
  onClickSearch(){
    let that = this;
    wx.showLoading({
      title: '加载中...',
    })
    if(this.data.stock_code){
      this.checkUserTokenValidate()
      var payload_data = {
        header: {

        },
        body: {
          stock_code: this.data.stock_code
        }
      }
      stock_api.validate_stock(payload_data).then(res=>{
        var result = res.result;
        var code = result.code;
        if(code == 200){
          if(result.data.code){
            wx.hideLoading();
            var stock_data = {
              stock_code: that.data.stock_code
            }
            wx.navigateTo({
                url: '/pages/detail/detail?stock=' + JSON.stringify(stock_data),
            });
          }
          else{
            Toast({
              context: that,
              selector: '#t-toast',
              message: '股票: ' + that.data.value + ', 不存在或异常',
            });
          }
        }
        else{
          Toast({
            context: this,
            selector: '#t-toast',
            message: result.data,
          });
        }
      })
    }
    else{
      Toast({
        context: this,
        selector: '#t-toast',
        message: '请先输入股票代码',
        theme: 'warning',
        direction: 'column'
      });
    }
  },
  setSearchValue(e){
    this.setData({
      stock_code: e.detail.value
    })
  }
})

