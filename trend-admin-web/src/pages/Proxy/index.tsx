import { Space } from 'antd'
import ProxyStats from './ProxyStats'
import ProxyConfig from './ProxyConfig'
import ProxyList from './ProxyList'

function Proxy() {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <h2 style={{ margin: 0 }}>IP 池管理</h2>

      {/* 统计信息 */}
      <ProxyStats />

      {/* 配置表单 */}
      <ProxyConfig />

      {/* IP 列表 */}
      <ProxyList />
    </Space>
  )
}

export default Proxy
