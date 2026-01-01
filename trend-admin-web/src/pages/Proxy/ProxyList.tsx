import { Card, Table, Button, Tag, Space, Modal, message } from 'antd'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { proxyApi } from '@/api/proxy'
import { formatCountdown } from '@/utils/format'
import { ReloadOutlined, DeleteOutlined } from '@ant-design/icons'
import { useState } from 'react'

function ProxyList() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const queryClient = useQueryClient()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['proxyIps', page, pageSize],
    queryFn: () => proxyApi.getIpList({ page, page_size: pageSize }),
    refetchInterval: 10000, // 每 10 秒刷新一次
  })

  const clearMutation = useMutation({
    mutationFn: proxyApi.clearIps,
    onSuccess: (result) => {
      message.success(`成功清空 ${result.cleared_count} 个 IP`)
      queryClient.invalidateQueries({ queryKey: ['proxyIps'] })
      queryClient.invalidateQueries({ queryKey: ['proxyStats'] })
    },
  })

  const handleClearAll = () => {
    Modal.confirm({
      title: '确认清空',
      content: '确定要清空所有 IP 吗？此操作不可逆！',
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => clearMutation.mutate(),
    })
  }

  const columns = [
    {
      title: 'IP 地址',
      dataIndex: 'ip',
      key: 'ip',
      width: 150,
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 100,
    },
    {
      title: '协议',
      dataIndex: 'protocol',
      key: 'protocol',
      width: 100,
      render: (protocol: string) => (
        <Tag color="blue">{protocol.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'TTL',
      dataIndex: 'ttl',
      key: 'ttl',
      width: 150,
      render: (ttl: number) => {
        if (!ttl || ttl <= 0) return <Tag color="default">已过期</Tag>
        const minutes = Math.floor(ttl / 60)
        const seconds = ttl % 60
        return <Tag color="processing">{minutes}分{seconds}秒</Tag>
      },
    },
    {
      title: '过期时间',
      dataIndex: 'expired_time_ts',
      key: 'expired_time_ts',
      width: 180,
      render: (timestamp: number) => formatCountdown(timestamp),
    },
    {
      title: '状态',
      dataIndex: 'is_valid',
      key: 'is_valid',
      width: 100,
      render: (isValid: boolean) => (
        isValid ? (
          <Tag color="success">有效</Tag>
        ) : (
          <Tag color="error">已过期</Tag>
        )
      ),
    },
  ]

  return (
    <Card
      title={`IP 池列表 (${data?.total || 0})`}
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            刷新
          </Button>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={handleClearAll}
            loading={clearMutation.isPending}
          >
            清空 IP 池
          </Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={data?.items || []}
        rowKey={(record) => `${record.ip}:${record.port}`}
        loading={isLoading}
        pagination={{
          current: page,
          pageSize: pageSize,
          total: data?.total || 0,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (newPage, newPageSize) => {
            setPage(newPage)
            setPageSize(newPageSize)
          },
        }}
      />
    </Card>
  )
}

export default ProxyList
