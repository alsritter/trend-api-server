import { Modal, Form, Input } from "antd";
import { useEffect } from "react";
import type { ClusterInfo } from "@/types/api";

interface EditClusterModalProps {
  visible: boolean;
  cluster: ClusterInfo | null;
  loading: boolean;
  onOk: (clusterName: string) => void;
  onCancel: () => void;
}

export function EditClusterModal({
  visible,
  cluster,
  loading,
  onOk,
  onCancel
}: EditClusterModalProps) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible && cluster) {
      form.setFieldsValue({ cluster_name: cluster.cluster_name });
    }
  }, [visible, cluster, form]);

  const handleOk = () => {
    form.validateFields().then((values) => {
      onOk(values.cluster_name);
    });
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="编辑聚簇名称"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={loading}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="cluster_name"
          label="聚簇名称"
          rules={[{ required: true, message: "请输入聚簇名称" }]}
        >
          <Input placeholder="请输入聚簇名称" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
