import { useState } from "react";
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
  const [formError, setFormError] = useState<string | null>(null);

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
    onSuccess: () => {
      setFormError(null);
      deviceQuery.refetch();
    },
    onError: (err: Error) => {
      setFormError(err.message);
    },
  });

  function handleSubmit(action: "retire" | "activate", formData: FormData) {
    setFormError(null);
    try {
      const input = schema.parse({
        reason: String(formData.get("reason") ?? ""),
      });
      mutateStatus.mutate({ action, reason: input.reason });
    } catch {
      setFormError("Reason is required");
    }
  }

  if (deviceQuery.isError) {
    return (
      <div className="mx-auto max-w-2xl p-6">
        <p className="text-red-600">
          Failed to load device: {deviceQuery.error?.message ?? "Unknown error"}
        </p>
      </div>
    );
  }

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

      {formError && (
        <p className="mt-4 text-sm text-red-600">{formError}</p>
      )}

      <form
        className="mt-6 flex gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit("retire", new FormData(e.currentTarget));
        }}
      >
        <input
          name="reason"
          placeholder="Reason"
          className="flex-1 rounded border p-2"
        />
        <button
          type="submit"
          disabled={isRetired || mutateStatus.isPending}
          className="rounded bg-red-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Retire
        </button>
      </form>

      <form
        className="mt-3 flex gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit("activate", new FormData(e.currentTarget));
        }}
      >
        <input
          name="reason"
          placeholder="Reason"
          className="flex-1 rounded border p-2"
        />
        <button
          type="submit"
          disabled={isActive || mutateStatus.isPending}
          className="rounded bg-green-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Activate
        </button>
      </form>
    </div>
  );
}
