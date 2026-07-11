import React from 'react';
import { Card, Button, Message } from '@arco-design/web-react';
import { useQuery } from '@tanstack/react-query';

const fetchApps = async () => {
  const res = await fetch('/v1/admin/apps');
  return res.json();
};

const Apps: React.FC = () => {
  const { data } = useQuery({ queryKey: ['apps'], queryFn: fetchApps });

  const handleCreateApp = async () => {
    const res = await fetch('/v1/admin/apps', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'new-app' }),
    });
    const result = await res.json();
    Message.success({ content: `API Key: ${result.api_key}`, duration: 10000 });
  };

  return (
    <Card title="应用管理" extra={<Button type="primary" onClick={handleCreateApp}>注册新应用</Button>}>
      <p>已注册应用: {data?.apps?.length || 0} 个</p>
    </Card>
  );
};

export default Apps;