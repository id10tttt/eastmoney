// pages/subscribe/subscribe.js
import subscribe_api from '../../api/subscribe.js'

Page({

  /**
   * 页面的初始数据
   */
  data: {
    default_value: 0,
    subscrlbe_list: [
      {
        'name': '',
        'price_total': '',
        'uuid': '',
        'type': '',
        'duration_time': ''
      }
    ]
  },
  onChangeRadio(e){
    this.setData({ 
      default_value: e.detail.value 
    });
  },
  getSubscribeList(){
    let payload_data = {
      header: {

      },
      body: {

      }
    }
    console.log('payload_data: ', payload_data)
    subscribe_api.get_subscribe_list(payload_data).then(res=>{
      let result = res.result
      let code = result.code
      let data = result.data
      if(code == 200){
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
    this.getSubscribeList()
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
    console.log('hello world')
    this.getSubscribeList()
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