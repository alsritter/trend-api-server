import { Card, Tabs, Table, Input, DatePicker, Space } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { contentsApi } from '@/api/contents'
import { useParams, useNavigate } from 'react-router-dom'
import { PLATFORM_OPTIONS } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'
import { useState } from 'react'
import NoteDetailDrawer from '@/components/NoteDetailDrawer'
import type { Note } from '@/types/api'

const { RangePicker } = DatePicker
const { Search } = Input

function Contents() {
  const { platform = 'xhs' } = useParams()
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['contents', platform, keyword, page, pageSize],
    queryFn: () =>
      contentsApi.getNotes(platform, {
        keyword,
        page,
        page_size: pageSize,
      }),
    enabled: !!platform,
  })

  const handleTabChange = (key: string) => {
    navigate(`/contents/${key}`)
    setPage(1)
    setKeyword('')
  }

  const handleSearch = (value: string) => {
    setKeyword(value)
    setPage(1)
  }

  const handleRowClick = (record: Note) => {
    setSelectedNote(record)
    setDrawerVisible(true)
  }

  const handleDrawerClose = () => {
    setDrawerVisible(false)
    setSelectedNote(null)
  }

  // 动态列配置（根据平台不同）
  const getColumns = () => {
    const commonColumns = [
      {
        title: 'ID',
        dataIndex: 'id',
        key: 'id',
        width: 80,
      },
      {
        title: '标题',
        dataIndex: 'title',
        key: 'title',
        ellipsis: true,
        width: 300,
      },
      {
        title: '作者',
        dataIndex: 'nickname',
        key: 'nickname',
        width: 150,
      },
    ]

    // 平台特定列
    if (platform === 'xhs') {
      return [
        ...commonColumns,
        { title: '点赞数', dataIndex: 'liked_count', key: 'liked_count', width: 100 },
        { title: '收藏数', dataIndex: 'collected_count', key: 'collected_count', width: 100 },
        { title: '评论数', dataIndex: 'comment_count', key: 'comment_count', width: 100 },
        {
          title: '发布时间',
          dataIndex: 'create_time',
          key: 'create_time',
          width: 180,
          render: formatDateTime,
        },
      ]
    } else if (platform === 'dy' || platform === 'ks') {
      return [
        ...commonColumns,
        { title: '播放量', dataIndex: 'video_play_count', key: 'video_play_count', width: 100 },
        { title: '点赞数', dataIndex: 'liked_count', key: 'liked_count', width: 100 },
        { title: '评论数', dataIndex: 'comment_count', key: 'comment_count', width: 100 },
        {
          title: '发布时间',
          dataIndex: 'create_time',
          key: 'create_time',
          width: 180,
          render: formatDateTime,
        },
      ]
    } else if (platform === 'bili') {
      return [
        ...commonColumns,
        { title: '播放量', dataIndex: 'video_play_count', key: 'video_play_count', width: 100 },
        { title: '弹幕数', dataIndex: 'video_danmaku', key: 'video_danmaku', width: 100 },
        { title: '评论数', dataIndex: 'video_comment', key: 'video_comment', width: 100 },
        {
          title: '发布时间',
          dataIndex: 'create_time',
          key: 'create_time',
          width: 180,
          render: formatDateTime,
        },
      ]
    }

    return commonColumns
  }

  const tabItems = PLATFORM_OPTIONS.map((opt) => ({
    key: opt.value,
    label: opt.label,
  }))

  return (
    <div>
      <Card>
        <Tabs
          activeKey={platform}
          items={tabItems}
          onChange={handleTabChange}
        />

        <Space style={{ marginBottom: 16 }}>
          <Search
            placeholder="搜索关键词"
            onSearch={handleSearch}
            style={{ width: 300 }}
            allowClear
          />
          <RangePicker placeholder={['开始日期', '结束日期']} />
        </Space>

        <Table
          columns={getColumns()}
          dataSource={data?.items || []}
          rowKey="id"
          loading={isLoading}
          onRow={(record) => ({
            onClick: () => handleRowClick(record),
            style: { cursor: 'pointer' },
          })}
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

      <NoteDetailDrawer
        visible={drawerVisible}
        onClose={handleDrawerClose}
        note={selectedNote}
        platform={platform}
      />
    </div>
  )
}

export default Contents
