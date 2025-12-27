import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  UserOutlined,
  GlobalOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
} from '@ant-design/icons'

const { Sider } = Layout

function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: '/accounts',
      icon: <UserOutlined />,
      label: '账号管理',
    },
    {
      key: '/proxy',
      icon: <GlobalOutlined />,
      label: 'IP 池管理',
    },
    {
      key: '/tasks',
      icon: <ThunderboltOutlined />,
      label: '任务管理',
    },
    {
      key: '/contents',
      icon: <DatabaseOutlined />,
      label: '数据查看',
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  return (
    <Sider width={200} theme="dark">
      <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 18, fontWeight: 'bold' }}>
        Trend Collector
      </div>
      <Menu
        mode="inline"
        theme="dark"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ borderRight: 0 }}
      />
    </Sider>
  )
}

export default Sidebar
