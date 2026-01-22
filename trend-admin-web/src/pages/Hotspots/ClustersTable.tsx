import { Table, Space, Button, Tag, Tooltip, Modal } from "antd";
import {
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloudDownloadOutlined
} from "@ant-design/icons";
import type { ClusterInfo } from "@/types/api";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { STATUS_MAP, PLATFORM_MAP } from "./constants";

interface ClustersTableProps {
  data: ClusterInfo[];
  loading: boolean;
  total: number;
  page: number;
  pageSize: number;
  expandedRowKeys: number[];
  searchKeyword: string;
  selectedRowKeys?: number[];
  onExpandChange: (expanded: boolean, record: ClusterInfo) => void;
  onEdit: (cluster: ClusterInfo) => void;
  onDelete: (clusterId: number, clusterName: string) => void;
  onValidateSuccess?: (cluster: ClusterInfo) => void;
  onTriggerCrawl?: (cluster: ClusterInfo) => void;
  onSelectChange?: (
    selectedRowKeys: React.Key[],
    selectedRows: ClusterInfo[]
  ) => void;
  onPageChange: (page: number, pageSize: number) => void;
  renderExpandedRow: (record: ClusterInfo) => React.ReactNode;
}

export function ClustersTable({
  data,
  loading,
  total,
  page,
  pageSize,
  expandedRowKeys,
  searchKeyword,
  selectedRowKeys,
  onExpandChange,
  onEdit,
  onDelete,
  onValidateSuccess,
  onTriggerCrawl,
  onSelectChange,
  onPageChange,
  renderExpandedRow
}: ClustersTableProps) {
  const columns: ColumnsType<ClusterInfo> = [
    {
      title: "ID",
      dataIndex: "id",
      key: "id",
      width: 80
    },
    {
      title: "聚簇名称",
      dataIndex: "cluster_name",
      key: "cluster_name",
      width: 250,
      filteredValue: searchKeyword ? [searchKeyword] : null,
      onFilter: (value, record) => {
        const keyword = value as string;
        return (
          record.cluster_name.toLowerCase().includes(keyword.toLowerCase()) ||
          record.keywords.some((k) =>
            k.toLowerCase().includes(keyword.toLowerCase())
          )
        );
      }
    },
    {
      title: "热点数量",
      dataIndex: "member_count",
      key: "member_count",
      width: 150,
      sorter: (a, b) => a.member_count - b.member_count
    },
    {
      title: "平台分布",
      dataIndex: "platforms",
      key: "platforms",
      width: 250,
      render: (platforms: ClusterInfo["platforms"]) => (
        <Space size={4} wrap>
          {platforms.map((p) => (
            <Tag key={p.platform} color="blue">
              {PLATFORM_MAP[p.platform] || p.platform} ({p.count})
            </Tag>
          ))}
        </Space>
      )
    },
    {
      title: "状态",
      dataIndex: "statuses",
      key: "statuses",
      width: 200,
      render: (statuses: string[]) => (
        <Space size={4} wrap>
          {statuses.map((status, idx) => {
            const statusInfo = STATUS_MAP[status];
            return (
              <Tag key={idx} color={statusInfo?.color || "default"}>
                {statusInfo?.label || status}
              </Tag>
            );
          })}
        </Space>
      )
    },
    {
      title: "最后更新",
      dataIndex: "last_hotspot_update",
      key: "last_hotspot_update",
      width: 180,
      sorter: (a, b) =>
        new Date(a.last_hotspot_update).getTime() -
        new Date(b.last_hotspot_update).getTime(),
      render: (date: string) => dayjs(date).format("YYYY-MM-DD HH:mm:ss")
    },
    {
      title: "操作",
      key: "action",
      width: 200,
      fixed: "right",
      render: (_, record) => (
        <Space size="small">
          {record.selected_hotspot_id && onValidateSuccess && (
            <Tooltip title="验证成功">
              <Button
                type="text"
                size="small"
                style={{ color: "#52c41a" }}
                icon={<CheckCircleOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onValidateSuccess(record);
                }}
              />
            </Tooltip>
          )}
          {record.selected_hotspot_id && onTriggerCrawl && (
            <Tooltip title="触发爬取">
              <Button
                type="text"
                size="small"
                style={{ color: "#1890ff" }}
                icon={<CloudDownloadOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  onTriggerCrawl(record);
                }}
              />
            </Tooltip>
          )}
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                onEdit(record);
              }}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                Modal.confirm({
                  title: "确认删除",
                  content: `确定要删除聚簇"${record.cluster_name}"吗？`,
                  onOk: () => onDelete(record.id, record.cluster_name)
                });
              }}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <Table
      columns={columns}
      dataSource={data}
      rowKey="id"
      loading={loading}
      rowSelection={
        onSelectChange
          ? {
              selectedRowKeys,
              onChange: onSelectChange,
              preserveSelectedRowKeys: true
            }
          : undefined
      }
      pagination={{
        current: page,
        pageSize: pageSize,
        total,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total) => `共 ${total} 个聚簇`,
        onChange: onPageChange
      }}
      expandable={{
        expandedRowKeys,
        onExpand: onExpandChange,
        expandedRowRender: renderExpandedRow
      }}
      onRow={(record) => ({
        onClick: (e) => {
          // 阻止点击操作按钮时触发行点击
          const target = e.target as HTMLElement;
          if (
            target.closest(".ant-btn") ||
            target.closest(".ant-checkbox-wrapper")
          ) {
            return;
          }
          const isExpanded = expandedRowKeys.includes(record.id);
          onExpandChange(!isExpanded, record);
        },
        style: { cursor: "pointer" }
      })}
      scroll={{ x: 1500 }}
    />
  );
}
