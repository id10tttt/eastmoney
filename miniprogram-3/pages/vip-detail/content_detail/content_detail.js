// pages/vip-detail/content_detail/content_detail.js
// 引入图表
import * as echarts from '../../../ec-canvas/echarts';

var option = []; //图表配置项 声明
// 初始化图表函数  开始
let chart2 = null;

function initChart2(canvas, width, height, dpr) {
  chart2 = echarts.init(canvas, null, {
    width: width,
    height: height,
    devicePixelRatio: dpr
  })
  canvas.setChart(chart2)
  return chart2;
}


Page({

  /**
   * 页面的初始数据
   */
  data: {
    ec2: {
      onInit: initChart2
    },
    detail_data: [],
    benchmark_data: {},
    benchmark_name: '',
    drawTimer: null,
    display_success: false
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    var benchmark_data = JSON.parse(options.benchmark_data)
    this.setData({
      stock_code: benchmark_data.stock_code,
      benchmark_id: benchmark_data.benchmark_id,
      detail_data: benchmark_data.data.data,
      benchmark_data: benchmark_data.data,
      benchmark_name: benchmark_data.data.benchmark
    })
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {
    this.initEchartView()
  },
  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    this.initEchartView()
  },
  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {

  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {},

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
  onResize() {

  },
  getEchartsOption(){
    let option = {}
    let date_value = Array()
    let date_data_value = Array()
    if (this.data.detail_data) {
      this.data.detail_data.map(res => {
        if(res.value){
          date_value.push(res.date)
          date_data_value.push(res.value.toFixed(2))
        }
      })
      option = {
        xAxis: {
          type: 'category',
          data: date_value,
          boundaryGap: false,
          axisLabel: {
            show: true,
            interval: 0,
            rotate: 45
          }
        },
        grid: {
          containLabel: true
        },
        tooltip: {
          show: true,
          trigger: 'axis',
          axisPointer: {
            type: 'line'
          }
        },
        toolbox: {
          show: true,
          feature: {
            magicType: {
              show: true,
              type: ["line", "bar"]
            },
            saveAsImage: {
              show: true
            },
          }
        },
        yAxis: {
          x: 'center',
          type: 'value',
          splitLine: {
            lineStyle: {
              type: 'dashed'
            }
          }
        },
        series: [{
            label: { //数据显示
              show: true,
              color: 'inherit',
              position: 'top',
              fontSize: 10,
            },
            data: date_data_value,
            type: 'line'
          }
        ]
      }
    }
    return option
  },
  initEchartView() {
    this.ecComponent = this.selectComponent('#mychart-dom-bar');
    this.ecComponent.init((canvas, width, height, dpr) => {
      // 获取组件的 canvas、width、height 后的回调函数
      // 在这里初始化图表
      const chart = echarts.init(canvas, null, {
        width: width,
        height: height,
        devicePixelRatio: dpr // new
      });
      console.log('start refresh...')
      let option = this.getEchartsOption()
      chart.setOption(option, true);

      // 将图表实例绑定到 this 上，可以在其他成员函数（如 dispose）中访问
      this.chart = chart;

      this.setData({
        isLoaded: true,
        isDisposed: false
      });

      // 注意这里一定要返回 chart 实例，否则会影响事件处理等
      return chart;
    });
  }
})
