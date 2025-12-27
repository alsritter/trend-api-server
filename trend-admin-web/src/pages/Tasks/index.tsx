import {
  Card,
  Table,
  Button,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  message,
} from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi } from '@/api/tasks'
import { PLATFORM_OPTIONS, CRAWLER_TYPE_OPTIONS, TASK_STATUS_MAP } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'
import { useState } from 'react'
import type { TaskCreateRequest } from '@/types/api'

function Tasks() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  // 创建任务
  const createMutation = useMutation({
    mutationFn: tasksApi.create,
    onSuccess: (data) => {
      message.success(`任务创建成功！任务ID: ${data.task_id}`)
      setIsModalOpen(false)
      form.resetFields()
      // 刷新任务列表（如果API已实现）
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  // 停止任务
  const stopMutation = useMutation({
    mutationFn: tasksApi.stop,
    onSuccess: () => {
      message.success('任务已停止')
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  const handleSubmit = (values: TaskCreateRequest) => {
    createMutation.mutate(values)
  }

  const handleStop = (taskId: string) => {
    Modal.confirm({
      title: '确认停止',
      content: `确定要停止任务 ${taskId} 吗？`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => stopMutation.mutate(taskId),
    })
  }

  const columns = [
    {
      title: '任务 ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
      render: (taskId: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{taskId}</span>
      ),
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 100,
      render: (platform: string) => <Tag color="blue">{platform.toUpperCase()}</Tag>,
    },
    {
      title: '类型',
      dataIndex: 'crawler_type',
      key: 'crawler_type',
      width: 120,
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const config = TASK_STATUS_MAP[status as keyof typeof TASK_STATUS_MAP] || {
          color: 'default',
          text: status,
        }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: formatDateTime,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: any) => (
        <Button
          type="link"
          danger
          onClick={() => handleStop(record.task_id)}
          disabled={['SUCCESS', 'FAILURE', 'REVOKED'].includes(record.status)}
        >
          停止
        </Button>
      ),
    },
  ]

  return (
    <div>
      <Card
        title="任务管理"
        extra={
          <Button type="primary" onClick={() => setIsModalOpen(true)}>
            创建任务
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="task_id"
          pagination={{ pageSize: 20 }}
          locale={{
            emptyText: '暂无任务数据。注意：任务列表 API 可能尚未实现，请通过任务 ID 查询单个任务状态。',
          }}
        />
      </Card>

      <Modal
        title="创建爬虫任务"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            enable_checkpoint: false,
            max_notes_count: 100,
            enable_comments: true,
            enable_sub_comments: false,
          }}
        >
          <Form.Item
            name="platform"
            label="平台"
            rules={[{ required: true, message: '请选择平台' }]}
          >
            <Select options={PLATFORM_OPTIONS} placeholder="请选择平台" />
          </Form.Item>

          <Form.Item
            name="crawler_type"
            label="爬虫类型"
            rules={[{ required: true, message: '请选择爬虫类型' }]}
          >
            <Select options={CRAWLER_TYPE_OPTIONS} placeholder="请选择爬虫类型" />
          </Form.Item>

          <Form.Item
            name="keywords"
            label="关键词"
            tooltip="多个关键词用逗号分隔"
          >
            <Input placeholder="例如: 美食,旅游,摄影" />
          </Form.Item>

          <Form.Item
            name="max_notes_count"
            label="最大采集数量"
            rules={[{ required: true, message: '请输入最大采集数量' }]}
          >
            <InputNumber min={1} max={10000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="enable_checkpoint"
            label="启用断点续爬"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="checkpoint_id"
            label="断点 ID"
            tooltip="用于恢复之前的爬取进度"
          >
            <Input placeholder="留空则自动生成" />
          </Form.Item>

          <Form.Item
            name="enable_comments"
            label="采集评论"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            name="enable_sub_comments"
            label="采集子评论"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Tasks
