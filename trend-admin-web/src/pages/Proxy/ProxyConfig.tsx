import { Card, Form, Input, InputNumber, Switch, Button, Alert, Space, message } from 'antd'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { proxyApi } from '@/api/proxy'
import type { ProxyConfigUpdateRequest } from '@/types/api'

function ProxyConfigForm() {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data: config, isLoading } = useQuery({
    queryKey: ['proxyConfig'],
    queryFn: proxyApi.getConfig,
  })

  const updateMutation = useMutation({
    mutationFn: proxyApi.updateConfig,
    onSuccess: () => {
      message.success('配置更新成功！请重启 Celery Worker 以应用更改')
      queryClient.invalidateQueries({ queryKey: ['proxyConfig'] })
      queryClient.invalidateQueries({ queryKey: ['proxyStats'] })
    },
    onError: (error: any) => {
      message.error(error.message || '配置更新失败')
    },
  })

  // 当配置加载完成后，设置表单初始值
  const handleFormChange = () => {
    if (config && !form.isFieldsTouched()) {
      form.setFieldsValue({
        enable_ip_proxy: config.enable_ip_proxy,
        ip_proxy_pool_count: config.ip_proxy_pool_count,
        ip_proxy_provider_name: config.ip_proxy_provider_name,
        kdl_secert_id: config.kdl_config?.kdl_secert_id || '',
        kdl_signature: config.kdl_config?.kdl_signature || '',
        kdl_user_name: config.kdl_config?.kdl_user_name || '',
        kdl_user_pwd: config.kdl_config?.kdl_user_pwd || '',
      })
    }
  }

  if (config && !form.isFieldsTouched()) {
    handleFormChange()
  }

  const handleSubmit = async (values: any) => {
    const updateData: ProxyConfigUpdateRequest = {}

    // 只提交有变化的字段
    Object.keys(values).forEach((key) => {
      if (values[key] !== undefined && values[key] !== '') {
        updateData[key as keyof ProxyConfigUpdateRequest] = values[key]
      }
    })

    if (Object.keys(updateData).length === 0) {
      message.warning('没有需要更新的配置')
      return
    }

    updateMutation.mutate(updateData)
  }

  const handleReset = () => {
    handleFormChange()
  }

  return (
    <Card title="代理配置" loading={isLoading}>
      <Alert
        message="配置说明"
        description="修改配置后需要重启 Celery Worker 才能生效！重启命令: supervisorctl restart celery-worker"
        type="warning"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          enable_ip_proxy: false,
          ip_proxy_pool_count: 2,
          ip_proxy_provider_name: 'kuaidaili',
        }}
      >
        <Form.Item
          name="enable_ip_proxy"
          label="启用 IP 代理"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name="ip_proxy_pool_count"
          label="IP 池大小"
          rules={[
            { required: true, message: '请输入 IP 池大小' },
            { type: 'number', min: 1, max: 100, message: '请输入 1-100 之间的数字' },
          ]}
        >
          <InputNumber min={1} max={100} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="ip_proxy_provider_name"
          label="IP 提供商"
        >
          <Input disabled value="kuaidaili" />
        </Form.Item>

        <Alert
          message="快代理配置"
          description="请填写快代理的认证信息，如不使用可留空"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form.Item
          name="kdl_secert_id"
          label="Secret ID"
        >
          <Input placeholder="请输入快代理 Secret ID" />
        </Form.Item>

        <Form.Item
          name="kdl_signature"
          label="Signature"
        >
          <Input placeholder="请输入快代理 Signature" />
        </Form.Item>

        <Form.Item
          name="kdl_user_name"
          label="用户名"
        >
          <Input placeholder="请输入快代理用户名" />
        </Form.Item>

        <Form.Item
          name="kdl_user_pwd"
          label="密码"
        >
          <Input.Password placeholder="请输入快代理密码" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              loading={updateMutation.isPending}
            >
              保存配置
            </Button>
            <Button onClick={handleReset}>
              重置
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  )
}

export default ProxyConfigForm
