import React from 'react';
import { Card, Table, Tag, Button, Space } from '@arco-design/web-react';
import { useQuery } from '@tanstack/react-query';

const fetchPolicies = async () => {
  const res = await fetch('/v1/admin/policies');
  return res.json();
};

const Policies: React.FC = () => {
  const { data, isLoading } = useQuery({ queryKey: ['policies'], queryFn: fetchPolicies });

  const columns = [
    { title: '策略名称', dataIndex: 'name', width: 200 },
    { title: '版本', dataIndex: 'version', width: 80 },
    {
      title: '状态', dataIndex: 'is_active', width: 100,
      render: (v: boolean) => <Tag color={v ? 'green' : 'gray'}>{v ? '生效中' : '已停用'}</Tag>,
    },
    { title: '操作', width: 150, render: () => <Button type="text" size="small">编辑</Button> },
  ];

  return (
    <Card title="策略管理">
      <Table columns={columns} data={data?.policies || []} loading={isLoading} rowKey="name" />
    </Card>
  );
};

export default Policies;