// pages/my/my.js
import Message from 'tdesign-miniprogram/message/index'
import user_api from '../../api/user.js'

const defaultAvatarUrl = 'https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0'


Page({

  /**
   * 页面的初始数据
   */
  data: {
    avatarUrl: defaultAvatarUrl,
    nick_name: '',
    vip_start_date: '',
    vip_end_date: '',
    theme: wx.getSystemInfoSync().theme,
  },

  onChooseAvatar(e) {
    const { avatarUrl } = e.detail 
    this.setData({
      avatarUrl,
    })
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    let that = this
    wx.onThemeChange((result) => {
      this.setData({
        theme: result.theme
      })
    })
    let payload_data = {

    }
    user_api.get_my_profile(payload_data).then(res=>{
      let result = res.result
      let code = result.code
      if(code == 200){
        let avatar_url = result.data.avatar_url
        if(!avatar_url){
          avatar_url = defaultAvatarUrl
        }
        that.setData({
          nick_name: result.data.nickname,
          avatarUrl: avatar_url,
          vip_start_date: result.data.start_date,
          vip_end_date: result.data.end_date
        })
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

  onChangeNickname(e){
    this.setData({
      nick_name: e.detail.value
    })
  },
  onBlurNickname(e){
    this.setData({
      nick_name: e.detail.value
    })
  },
  onSaveMyProfile(){
    try{
      let image_binary = wx.getFileSystemManager().readFileSync(this.data.avatarUrl, "base64")
      this.setData({
        image_binary: image_binary
      })
    }catch(e){
      console.error(e)
      let image_binary = ''
      this.setData({
        image_binary: image_binary
      })
    }
    let that = this
    let payload_data = {
      header: {

      },
      body: {
        nick_name: this.data.nick_name,
        avatar_url: this.data.avatarUrl,
        avatar_binary: this.data.image_binary
      }
    }
    user_api.update_my_profile(payload_data).then(res=>{
      let result = res.result
      let code = result.code
      if(code == 200){
        Message.success({
          context: that,
          offset: [20, 32],
          duration: 5000,
          content: '更新成功',
        });
        wx.navigateBack()
      }
      else{
        Message.error({
          context: that,
          offset: [20, 32],
          duration: 5000,
          content: '更新失败',
        });
      }
    })
  }
})
