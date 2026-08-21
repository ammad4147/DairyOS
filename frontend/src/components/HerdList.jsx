import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

const fetchHerd = async () => {
  const response = await api.get('/herd');
  return response.data;
};

export default function HerdList() {
  const { data: herd, isLoading, isError } = useQuery({
    queryKey: ['herd'], 
    queryFn: fetchHerd,
  });

  if (isLoading) return <div>Loading records...</div>;
  if (isError) return <div>Error fetching herd data.</div>;

  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-xl font-bold mb-4">Active Herd</h2>
      <ul>
        {herd.map((animal) => (
          <li key={animal.id} className="border-b py-2">
            <strong>{animal.id}</strong> - {animal.name} ({animal.status})
          </li>
        ))}
      </ul>
    </div>
  );
}
