import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  message
} from "antd";
import {
  SearchOutlined,
  ReloadOutlined
} from "@ant-design/icons";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { hotspotsApi } from "@/api/hotspots";
import type {
  HotspotDetail,
  HotspotStatus,
  ListHotspotsRequest
} from "@/types/api";
import "./styles.css";
import { getHotspotTableColumns, STATUS_MAP } from "./components/HotspotTableColumns";
import { HotspotDetailModal } from "./components/HotspotDetailModal";
import { ClusterHotspotsModal } from "./components/ClusterHotspotsModal";

const { Search } = Input;

function Hotspots() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<HotspotStatus | undefined>(
    undefined
  );
  const [keywordSearch, setKeywordSearch] = useState<string>("");
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [clusterModalVisible, setClusterModalVisible] = useState(false);
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotDetail | null>(
    null
  );
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(
    null
  );

  // 查询参数
  const queryParams: ListHotspotsRequest = {
    page,
    page_size: pageSize,
    status: statusFilter,
    keyword: keywordSearch || undefined
  };

  // 获取热点列表
  const {
    data: hotspotsData,
    isLoading,
    refetch
  } = useQuery({
    queryKey: ["hotspots", queryParams],
    queryFn: () => hotspotsApi.list(queryParams)
  });

  // 删除热点
  const deleteMutation = useMutation({
    mutationFn: hotspotsApi.delete,
    onSuccess: (data) => {
      message.success(data.message);
      refetch();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    }
  });

  // 查看详情
  const handleViewDetail = async (record: HotspotDetail) => {
    setSelectedHotspot(record);
    setDetailModalVisible(true);
  };

  // 查看同簇热点
  const handleViewCluster = (clusterId: number) => {
    setSelectedClusterId(clusterId);
    setClusterModalVisible(true);
  };

  // 删除热点
  const handleDelete = (hotspotId: number) => {
    deleteMutation.mutate(hotspotId);
  };

  // 搜索
  const handleSearch = (value: string) => {
    setKeywordSearch(value);
    setPage(1);
  };

  // 重置过滤
  const handleReset = () => {
    setStatusFilter(undefined);
    setKeywordSearch("");
    setPage(1);
  };

  // 表格列定义
  const columns = getHotspotTableColumns({
    onViewDetail: handleViewDetail,
    onDelete: handleDelete,
    onViewCluster: handleViewCluster,
    isDeleting: deleteMutation.isPending
  });

  return (
    <div className="hotspots-container">
      <Card>
        {/* 顶部筛选栏 */}
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Space wrap>
            <Search
              placeholder="搜索热词..."
              onSearch={handleSearch}
              style={{ width: 300 }}
              allowClear
              enterButton={<SearchOutlined />}
            />
            <Select
              placeholder="选择状态"
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 150 }}
              allowClear
              options={[
                { label: "全部状态", value: undefined },
                ...Object.entries(STATUS_MAP).map(([value, { label }]) => ({
                  label,
                  value
                }))
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              刷新
            </Button>
            <Button onClick={handleReset}>重置</Button>
          </Space>
        </Space>

        {/* 数据表格 */}
        <Table
          columns={columns}
          dataSource={hotspotsData?.items || []}
          rowKey="id"
          loading={isLoading}
          scroll={{ x: 1500 }}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: hotspotsData?.total || 0,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (newPage, newPageSize) => {
              setPage(newPage);
              setPageSize(newPageSize);
            }
          }}
        />
      </Card>

      {/* 详情弹窗 */}
      <HotspotDetailModal
        visible={detailModalVisible}
        hotspot={selectedHotspot}
        onClose={() => {
          setDetailModalVisible(false);
          setSelectedHotspot(null);
        }}
      />

      {/* 同簇热点弹窗 */}
      <ClusterHotspotsModal
        visible={clusterModalVisible}
        clusterId={selectedClusterId}
        onClose={() => {
          setClusterModalVisible(false);
          setSelectedClusterId(null);
        }}
      />
    </div>
  );
}

export default Hotspots;
