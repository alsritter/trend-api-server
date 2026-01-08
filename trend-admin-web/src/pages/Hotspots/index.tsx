import { Card, Space, Button, message } from "antd";
import { ReloadOutlined, MergeCellsOutlined } from "@ant-design/icons";
import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { clustersApi } from "@/api/clusters";
import type { ClusterInfo, HotspotDetail } from "@/types/api";
import type { Dayjs } from "dayjs";
import { HotspotsFilter } from "./HotspotsFilter";
import { ClustersTable } from "./ClustersTable";
import { ClusterExpandedRow } from "./ClusterExpandedRow";
import { HotspotDetailDrawer } from "./HotspotDetailDrawer";
import { EditClusterModal } from "./EditClusterModal";
import { MergeClustersModal } from "./MergeClustersModal";

function Hotspots() {
  const [expandedRowKeys, setExpandedRowKeys] = useState<number[]>([]);

  // 过滤条件状态
  const [filterStatus, setFilterStatus] = useState<string[]>([]);
  const [excludeStatus, setExcludeStatus] = useState<string[]>([]);
  const [filterPlatforms, setFilterPlatforms] = useState<string[]>([]);
  const [filterDateRange, setFilterDateRange] = useState<
    [Dayjs | null, Dayjs | null] | null
  >(null);
  const [searchKeyword, setSearchKeyword] = useState<string>("");

  // 详情抽屉状态
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotDetail | null>(
    null
  );

  // 编辑聚簇名称
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingCluster, setEditingCluster] = useState<ClusterInfo | null>(
    null
  );

  // 合并聚簇
  const [mergeModalVisible, setMergeModalVisible] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([]);
  const [selectedClusters, setSelectedClusters] = useState<ClusterInfo[]>([]);

  // 查询聚簇列表
  const {
    data: clustersData,
    isLoading: clustersLoading,
    refetch: refetchClusters
  } = useQuery({
    queryKey: [
      "clusters",
      filterStatus,
      excludeStatus,
      filterPlatforms,
      filterDateRange,
      searchKeyword
    ],
    queryFn: async () => {
      const params: any = {};
      if (filterStatus.length > 0) params.status = filterStatus.join(",");
      if (excludeStatus.length > 0)
        params.exclude_status = excludeStatus.join(",");
      if (filterPlatforms.length > 0)
        params.platforms = filterPlatforms.join(",");
      if (filterDateRange?.[0])
        params.start_time = filterDateRange[0].toISOString();
      if (filterDateRange?.[1])
        params.end_time = filterDateRange[1].toISOString();
      if (searchKeyword) params.keyword = searchKeyword;

      return clustersApi.list(params);
    }
  });

  // 更新聚簇名称
  const updateClusterMutation = useMutation({
    mutationFn: ({
      clusterId,
      clusterName
    }: {
      clusterId: number;
      clusterName: string;
    }) => clustersApi.update(clusterId, { cluster_name: clusterName }),
    onSuccess: () => {
      message.success("聚簇名称更新成功");
      setEditModalVisible(false);
      setEditingCluster(null);
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`更新失败: ${error.message}`);
    }
  });

  // 删除聚簇
  const deleteClusterMutation = useMutation({
    mutationFn: (clusterId: number) => clustersApi.delete(clusterId),
    onSuccess: () => {
      message.success("聚簇删除成功");
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message}`);
    }
  });

  // 合并聚簇
  const mergeClustersMutation = useMutation({
    mutationFn: (data: {
      source_cluster_ids: number[];
      target_cluster_name?: string;
    }) => clustersApi.merge(data),
    onSuccess: () => {
      message.success("聚簇合并成功");
      setMergeModalVisible(false);
      setSelectedRowKeys([]);
      setSelectedClusters([]);
      refetchClusters();
    },
    onError: (error: any) => {
      message.error(`合并失败: ${error.message}`);
    }
  });

  // 重置过滤条件
  const handleResetFilters = () => {
    setFilterStatus([]);
    setExcludeStatus([]);
    setFilterPlatforms([]);
    setFilterDateRange(null);
    setSearchKeyword("");
  };

  // 处理展开/收起聚簇
  const handleExpandChange = (expanded: boolean, record: ClusterInfo) => {
    if (expanded) {
      setExpandedRowKeys([...expandedRowKeys, record.id]);
    } else {
      setExpandedRowKeys(expandedRowKeys.filter((key) => key !== record.id));
    }
  };

  // 处理编辑聚簇
  const handleEdit = (cluster: ClusterInfo) => {
    setEditingCluster(cluster);
    setEditModalVisible(true);
  };

  // 处理删除聚簇
  const handleDelete = (clusterId: number) => {
    deleteClusterMutation.mutate(clusterId);
  };

  // 处理编辑确认
  const handleEditConfirm = (clusterName: string) => {
    if (editingCluster) {
      updateClusterMutation.mutate({
        clusterId: editingCluster.id,
        clusterName
      });
    }
  };

  // 处理编辑取消
  const handleEditCancel = () => {
    setEditModalVisible(false);
    setEditingCluster(null);
  };

  // 处理查看热点详情
  const handleViewHotspotDetail = (hotspot: HotspotDetail) => {
    setSelectedHotspot(hotspot);
    setDetailDrawerVisible(true);
  };

  // 处理关闭详情抽屉
  const handleCloseDetailDrawer = () => {
    setDetailDrawerVisible(false);
    setSelectedHotspot(null);
  };

  // 处理行选择
  const handleSelectChange = (
    selectedKeys: React.Key[],
    selectedRows: ClusterInfo[]
  ) => {
    setSelectedRowKeys(selectedKeys as number[]);
    setSelectedClusters(selectedRows);
  };

  // 处理打开合并模态框
  const handleOpenMergeModal = () => {
    if (selectedRowKeys.length < 2) {
      message.warning("请至少选择2个聚簇进行合并");
      return;
    }
    setMergeModalVisible(true);
  };

  // 处理合并确认
  const handleMergeConfirm = (targetClusterName?: string) => {
    mergeClustersMutation.mutate({
      source_cluster_ids: selectedRowKeys,
      target_cluster_name: targetClusterName
    });
  };

  // 处理合并取消
  const handleMergeCancel = () => {
    setMergeModalVisible(false);
  };

  return (
    <div style={{ padding: "24px" }}>
      <Card
        title="热点聚簇管理"
        extra={
          <Space>
            <Button
              icon={<MergeCellsOutlined />}
              onClick={handleOpenMergeModal}
              disabled={selectedRowKeys.length < 2}
            >
              合并聚簇 ({selectedRowKeys.length})
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetchClusters()}
              loading={clustersLoading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <HotspotsFilter
          searchKeyword={searchKeyword}
          filterStatus={filterStatus}
          excludeStatus={excludeStatus}
          filterPlatforms={filterPlatforms}
          filterDateRange={filterDateRange}
          onSearchChange={setSearchKeyword}
          onStatusChange={setFilterStatus}
          onExcludeStatusChange={setExcludeStatus}
          onPlatformsChange={setFilterPlatforms}
          onDateRangeChange={setFilterDateRange}
          onReset={handleResetFilters}
        />

        <ClustersTable
          data={clustersData?.items || []}
          loading={clustersLoading}
          total={clustersData?.count || 0}
          expandedRowKeys={expandedRowKeys}
          searchKeyword={searchKeyword}
          selectedRowKeys={selectedRowKeys}
          onExpandChange={handleExpandChange}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSelectChange={handleSelectChange}
          renderExpandedRow={(record) => (
            <ClusterExpandedRow
              clusterId={record.id}
              onViewDetail={handleViewHotspotDetail}
            />
          )}
        />
      </Card>

      <HotspotDetailDrawer
        visible={detailDrawerVisible}
        hotspot={selectedHotspot}
        onClose={handleCloseDetailDrawer}
      />

      <EditClusterModal
        visible={editModalVisible}
        cluster={editingCluster}
        loading={updateClusterMutation.isPending}
        onOk={handleEditConfirm}
        onCancel={handleEditCancel}
      />

      <MergeClustersModal
        visible={mergeModalVisible}
        clusters={selectedClusters}
        loading={mergeClustersMutation.isPending}
        onOk={handleMergeConfirm}
        onCancel={handleMergeCancel}
      />
    </div>
  );
}

export default Hotspots;
