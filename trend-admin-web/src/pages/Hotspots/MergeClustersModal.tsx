import { Modal, Form, Input, List, Tag } from "antd";
import type { ClusterInfo } from "@/types/api";

interface MergeClustersModalProps {
  visible: boolean;
  clusters: ClusterInfo[];
  loading: boolean;
  onOk: (targetClusterName?: string) => void;
  onCancel: () => void;
}

export function MergeClustersModal({
  visible,
  clusters,
  loading,
  onOk,
  onCancel
}: MergeClustersModalProps) {
  const [form] = Form.useForm();

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      onOk(values.cluster_name || undefined);
      form.resetFields();
    } catch (error) {
      // 验证失败，不执行任何操作
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  // 计算合并后的总热点数
  const totalHotspots = clusters.reduce(
    (sum, cluster) => sum + cluster.member_count,
    0
  );

  return (
    <Modal
      title={`合并聚簇 (${clusters.length}个)`}
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={loading}
      width={600}
    >
      <div style={{ marginBottom: 16 }}>
        <p style={{ marginBottom: 8 }}>
          将以下 <strong>{clusters.length}</strong> 个聚簇合并为一个，共包含{" "}
          <strong>{totalHotspots}</strong> 个热点：
        </p>
        <List
          size="small"
          bordered
          dataSource={clusters}
          renderItem={(cluster) => (
            <List.Item>
              <div style={{ width: "100%" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center"
                  }}
                >
                  <span>
                    <strong>{cluster.cluster_name}</strong>
                  </span>
                  <Tag color="blue">{cluster.member_count} 个热点</Tag>
                </div>
                {cluster.keywords.length > 0 && (
                  <div
                    style={{ marginTop: 4, fontSize: 12, color: "#666" }}
                  >
                    关键词: {cluster.keywords.slice(0, 5).join(", ")}
                    {cluster.keywords.length > 5 && " ..."}
                  </div>
                )}
              </div>
            </List.Item>
          )}
        />
      </div>

      <Form form={form} layout="vertical">
        <Form.Item
          name="cluster_name"
          label="合并后的聚簇名称（可选）"
          extra="留空将使用第一个聚簇的名称"
        >
          <Input
            placeholder={`默认使用: ${clusters[0]?.cluster_name || ""}`}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
