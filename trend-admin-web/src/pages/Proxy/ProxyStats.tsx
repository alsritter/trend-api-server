import { Card, Row, Col, Statistic } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { proxyApi } from '@/api/proxy'
import {
  GlobalOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloudServerOutlined,
} from '@ant-design/icons'

function ProxyStats() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['proxyStats'],
    queryFn: proxyApi.getStats,
    refetchInterval: 10000, // 每 10 秒刷新
  })

  return (
    <Row gutter={16}>
      <Col span={6}>
        <Card loading={isLoading}>
          <Statistic
            title="总 IP 数"
            value={stats?.total_ips || 0}
            prefix={<GlobalOutlined />}
            suffix="个"
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card loading={isLoading}>
          <Statistic
            title="有效 IP 数"
            value={stats?.valid_ips || 0}
            prefix={<CheckCircleOutlined />}
            suffix="个"
            valueStyle={{ color: '#3f8600' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card loading={isLoading}>
          <Statistic
            title="已过期 IP 数"
            value={stats?.expired_ips || 0}
            prefix={<CloseCircleOutlined />}
            suffix="个"
            valueStyle={{ color: '#cf1322' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card loading={isLoading}>
          <Statistic
            title="提供商"
            value={stats?.provider_name || 'unknown'}
            prefix={<CloudServerOutlined />}
          />
        </Card>
      </Col>
    </Row>
  )
}

export default ProxyStats
