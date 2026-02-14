import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { useApi, type ProjectedDevice, type ListResponse } from "../lib/api"; // CHANGED

export function DevicesPage() {
  const [page, setPage] = useState(0);
  const limit = 10;
  const offset = page * limit;
  const { request } = useApi();
  const navigate = useNavigate();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["devices", { limit, offset }],
    queryFn: () =>
      request<ListResponse<ProjectedDevice>>( // CHANGED
        `/api/v1/devices/projected?limit=${limit}&offset=${offset}` // CHANGED
      ),
  });

  const total = data?.page.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Devices</h2>
        <Link
          className="rounded bg-black px-4 py-2 text-white"
          to="/devices/new"
        >
          Add device
        </Link>
      </div>

      <div className="mt-4 overflow-x-auto rounded border">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-3">ID</th>
              <th className="p-3">Owner</th> {/* NEW */}
              <th className="p-3">MAC</th>
              <th className="p-3">Status</th>
              <th className="p-3">Created</th>
              <th className="p-3">Updated</th>
              <th className="p-3">Version</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td className="p-3" colSpan={7}>
                  Loading...
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td className="p-3 text-red-600" colSpan={7}>
                  Failed to load devices: {error?.message ?? "Unknown error"}
                </td>
              </tr>
            )}
            {!isLoading && !isError && data?.data.length === 0 && (
              <tr>
                <td className="p-3 text-center text-gray-500" colSpan={7}>
                  No devices yet. Click "Add device" to create one.
                </td>
              </tr>
            )}
            {data?.data.map((d) => (
              <tr
                key={d.id}
                className="cursor-pointer border-t hover:bg-gray-50"
                onClick={() => navigate(`/devices/${d.id}`)}
              >
                <td className="p-3 font-mono text-xs">{d.id.slice(0, 8)}…</td>
                <td className="p-3">{d.owner_email ?? "—"}</td> {/* NEW */}
                <td className="p-3 font-mono text-xs">{d.mac_address}</td>
                <td className="p-3">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      d.status === "active"
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {d.status}
                  </span>
                </td>
                <td className="p-3 text-xs">
                  {new Date(d.created_at).toLocaleString()}
                </td>
                <td className="p-3 text-xs">
                  {new Date(d.updated_at).toLocaleString()}
                </td>
                <td className="p-3">{d.version}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <button
          className="rounded border px-3 py-1 disabled:opacity-50"
          disabled={page === 0}
          onClick={() => setPage((p) => Math.max(0, p - 1))}
        >
          Prev
        </button>
        <div className="flex gap-2">
          {Array.from({ length: pageCount }).map((_, idx) => (
            <button
              key={idx}
              className={`rounded px-3 py-1 ${
                idx === page ? "bg-black text-white" : "border"
              }`}
              onClick={() => setPage(idx)}
            >
              {idx + 1}
            </button>
          ))}
        </div>
        <button
          className="rounded border px-3 py-1 disabled:opacity-50"
          disabled={page >= pageCount - 1}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
