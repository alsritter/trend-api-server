import { Layout } from 'antd'

const { Header: AntHeader } = Layout

function Header() {
  return (
    <AntHeader style={{ background: '#fff', padding: '0 24px', boxShadow: '0 1px 4px rgba(0,21,41,.08)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '100%' }}>
        <div style={{ fontSize: 18, fontWeight: 500 }}>
          Trend API Server 管理后台
        </div>
        <div>
          <span style={{ marginRight: 16 }}>欢迎使用</span>
        </div>
      </div>
    </AntHeader>
  )
}

export default Header
