import { useMutation, useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { useParams } from "react-router-dom";

import { useApi, type DataResponse, type Device } from "../lib/api";

const schema = z.object({
  reason: z.string().min(1),
});

export function DeviceDetailPage() {
  const { deviceId } = useParams();
  const { request } = useApi();

  const deviceQuery = useQuery({
    queryKey: ["device", deviceId],
    queryFn: () => request<DataResponse<Device>>(`/api/v1/devices/${deviceId}`),
    enabled: !!deviceId,
  });

  const mutateStatus = useMutation({
    mutationFn: (input: { action: "retire" | "activate"; reason: string }) =>
      request<DataResponse<Device>>(
        `/api/v1/devices/${deviceId}/${input.action}`,
        {
          method: "POST",
          body: JSON.stringify({
            reason: input.reason,
            expected_version: deviceQuery.data?.data.version ?? 1,
          }),
        }
      ),
    onSuccess: () => deviceQuery.refetch(),
  });

  const device = deviceQuery.data?.data;

  if (!device) return <div className="p-6">Loading...</div>;

  const isActive = device.status === "active";
  const isRetired = device.status === "retired";

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h2 className="text-xl font-semibold">Device details</h2>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>ID</div>
        <div>{device.id}</div>
        <div>MAC</div>
        <div>{device.mac_address}</div>
        <div>Status</div>
        <div>{device.status}</div>
        <div>Created</div>
        <div>{new Date(device.created_at).toLocaleString()}</div>
        <div>Updated</div>
        <div>{new Date(device.updated_at).toLocaleString()}</div>
        <div>Version</div>
        <div>{device.version}</div>
      </div>

      <form
        className="mt-6 flex gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          const form = new FormData(e.currentTarget);
          const input = schema.parse({
            reason: String(form.get("reason") ?? ""),
          });
          mutateStatus.mutate({ action: "retire", reason: input.reason });
        }}
      >
        <input
          name="reason"
          placeholder="Reason"
          className="flex-1 rounded border p-2"
        />
        <button
          type="submit"
          disabled={isRetired}
          className="rounded bg-red-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Retire
        </button>
      </form>

      <form
        className="mt-3 flex gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          const form = new FormData(e.currentTarget);
          const input = schema.parse({
            reason: String(form.get("reason") ?? ""),
          });
          mutateStatus.mutate({ action: "activate", reason: input.reason });
        }}
      >
        <input
          name="reason"
          placeholder="Reason"
          className="flex-1 rounded border p-2"
        />
        <button
          type="submit"
          disabled={isActive}
          className="rounded bg-green-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Activate
        </button>
      </form>
    </div>
  );
}
