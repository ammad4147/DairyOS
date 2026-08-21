import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import api from '../services/api';

export default function AIForm() {
  const [formData, setFormData] = useState({
    cow_id: '',
    bull_id: '',
    date: new Date().toISOString().split('T')[0],
    technician: '',
    notes: ''
  });

  // useMutation handles the POST request lifecycle
  const mutation = useMutation({
    mutationFn: (newRecord) => {
      return api.post('/ai-records', newRecord);
    },
    onSuccess: (data) => {
      alert(data.data.message);
      // Reset form on success
      setFormData({
        cow_id: '',
        bull_id: '',
        date: new Date().toISOString().split('T')[0],
        technician: '',
        notes: ''
      });
    },
    onError: (error) => {
      alert('Failed to save record. Check the console for details.');
      console.error(error);
    }
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className="max-w-md p-6 bg-white rounded shadow-md border-t-4 border-green-600">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Log AI Event</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Cow ID (Tag)</label>
          <input 
            type="text" 
            name="cow_id" 
            required 
            value={formData.cow_id} 
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Bull ID / Semen Batch</label>
          <input 
            type="text" 
            name="bull_id" 
            required 
            value={formData.bull_id} 
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Date of Insemination</label>
          <input 
            type="date" 
            name="date" 
            required 
            value={formData.date} 
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Technician</label>
          <input 
            type="text" 
            name="technician" 
            required 
            value={formData.technician} 
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Notes (Optional)</label>
          <textarea 
            name="notes" 
            value={formData.notes} 
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
            rows="3"
          ></textarea>
        </div>

        <button 
          type="submit" 
          disabled={mutation.isPending}
          className="w-full bg-green-600 text-white p-2 rounded hover:bg-green-700 transition disabled:bg-gray-400"
        >
          {mutation.isPending ? 'Saving...' : 'Save AI Record'}
        </button>
      </form>
    </div>
  );
}
