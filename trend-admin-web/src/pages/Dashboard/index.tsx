import { Card, Row, Col, Statistic, Tag, Spin } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { systemApi } from '@/api/system'
import {
  ApiOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'

function Dashboard() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: systemApi.getHealth,
    refetchInterval: 5000, // 每 5 秒刷新
  })

  const { data: dbStats, isLoading: statsLoading } = useQuery({
    queryKey: ['databaseStats'],
    queryFn: systemApi.getDatabaseStats,
    refetchInterval: 30000, // 每 30 秒刷新
  })

  const getStatusTag = (status: string) => {
    return status === 'healthy' ? (
      <Tag color="success">正常</Tag>
    ) : (
      <Tag color="error">异常</Tag>
    )
  }

  if (healthLoading || statsLoading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  }

  // 计算总数据量
  const totalNotes = Object.values(dbStats || {}).reduce(
    (sum: number, platform: any) => sum + (platform.notes || 0),
    0
  )
  const totalComments = Object.values(dbStats || {}).reduce(
    (sum: number, platform: any) => sum + (platform.comments || 0),
    0
  )
  const totalCreators = Object.values(dbStats || {}).reduce(
    (sum: number, platform: any) => sum + (platform.creators || 0),
    0
  )

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>系统概览</h2>

      {/* 系统健康状态 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="API Server"
              value={health?.api_server || 'unknown'}
              prefix={<ApiOutlined />}
              valueRender={() => getStatusTag(health?.api_server || 'unknown')}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="MySQL"
              value={health?.mysql || 'unknown'}
              prefix={<DatabaseOutlined />}
              valueRender={() => getStatusTag(health?.mysql || 'unknown')}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Redis"
              value={health?.redis || 'unknown'}
              prefix={<CloudServerOutlined />}
              valueRender={() => getStatusTag(health?.redis || 'unknown')}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Celery"
              value={health?.celery || 'unknown'}
              prefix={<ThunderboltOutlined />}
              valueRender={() => getStatusTag(health?.celery || 'unknown')}
            />
          </Card>
        </Col>
      </Row>

      {/* 数据统计 */}
      <Row gutter={16}>
        <Col span={8}>
          <Card>
            <Statistic
              title="总笔记/视频数"
              value={totalNotes}
              suffix="条"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="总评论数"
              value={totalComments}
              suffix="条"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="总创作者数"
              value={totalCreators}
              suffix="人"
            />
          </Card>
        </Col>
      </Row>

      {/* 平台数据详情 */}
      <Card title="平台数据详情" style={{ marginTop: 24 }}>
        <Row gutter={16}>
          {Object.entries(dbStats || {}).map(([platform, data]: [string, any]) => (
            <Col span={8} key={platform} style={{ marginBottom: 16 }}>
              <Card size="small" title={platform.toUpperCase()}>
                <p>笔记/视频: {data.notes || 0}</p>
                <p>评论: {data.comments || 0}</p>
                <p>创作者: {data.creators || 0}</p>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  )
}

export default Dashboard
