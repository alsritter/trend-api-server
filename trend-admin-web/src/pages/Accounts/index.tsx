import { Card, Table, Button, Space, Tag, Modal, Form, Input, Select, message } from 'antd'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { accountsApi } from '@/api/accounts'
import { PLATFORM_OPTIONS, ACCOUNT_STATUS_MAP } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'
import { useState } from 'react'
import type { Account } from '@/types/api'

function Accounts() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState<Account | null>(null)
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.list({ page: 1, page_size: 100 }),
  })

  const createMutation = useMutation({
    mutationFn: accountsApi.create,
    onSuccess: () => {
      message.success('账号创建成功')
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      setIsModalOpen(false)
      form.resetFields()
      setEditingAccount(null)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      accountsApi.update(id, data),
    onSuccess: () => {
      message.success('账号更新成功')
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      setIsModalOpen(false)
      form.resetFields()
      setEditingAccount(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: accountsApi.delete,
    onSuccess: () => {
      message.success('账号删除成功')
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
  })

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '账号名称', dataIndex: 'account_name', key: 'account_name' },
    {
      title: '平台',
      dataIndex: 'platform_name',
      key: 'platform_name',
      render: (platform: string) => <Tag color="blue">{platform.toUpperCase()}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: number) => {
        const config = ACCOUNT_STATUS_MAP[status as keyof typeof ACCOUNT_STATUS_MAP]
        return <Tag color={config?.color}>{config?.text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      render: formatDateTime,
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      key: 'update_time',
      render: formatDateTime,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Account) => (
        <Space>
          <Button
            type="link"
            onClick={() => {
              setEditingAccount(record)
              form.setFieldsValue({
                account_name: record.account_name,
                platform_name: record.platform_name,
                status: record.status,
              })
              setIsModalOpen(true)
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            onClick={() => {
              Modal.confirm({
                title: '确认删除',
                content: `确定要删除账号 "${record.account_name}" 吗？`,
                onOk: () => deleteMutation.mutate(record.id),
              })
            }}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  const handleSubmit = async (values: any) => {
    if (editingAccount) {
      // 编辑模式
      updateMutation.mutate({
        id: editingAccount.id,
        data: values,
      })
    } else {
      // 创建模式
      createMutation.mutate(values)
    }
  }

  return (
    <div>
      <Card
        title="账号管理"
        extra={
          <Button type="primary" onClick={() => setIsModalOpen(true)}>
            新增账号
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editingAccount ? '编辑账号' : '新增账号'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
          setEditingAccount(null)
        }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="account_name"
            label="账号名称"
            rules={[{ required: !editingAccount, message: '请输入账号名称' }]}
          >
            <Input placeholder="请输入账号名称" disabled={!!editingAccount} />
          </Form.Item>
          <Form.Item
            name="platform_name"
            label="平台"
            rules={[{ required: !editingAccount, message: '请选择平台' }]}
          >
            <Select options={PLATFORM_OPTIONS} placeholder="请选择平台" disabled={!!editingAccount} />
          </Form.Item>
          <Form.Item
            name="cookies"
            label="Cookies"
            rules={[{ required: !editingAccount, message: '请输入 Cookies' }]}
          >
            <Input.TextArea
              rows={4}
              placeholder={editingAccount ? '留空则不更新 Cookies' : '请粘贴登录后的 Cookies'}
            />
          </Form.Item>
          {editingAccount && (
            <Form.Item
              name="status"
              label="账号状态"
            >
              <Select
                options={[
                  { label: '正常', value: 0 },
                  { label: '失效', value: -1 },
                ]}
                placeholder="请选择账号状态"
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default Accounts
