import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { useNavigate } from "react-router-dom";

import { useApi, type DataResponse, type Device } from "../lib/api";

const schema = z.object({
  mac_address: z.string().min(1),
});

export function NewDevicePage() {
  const { request } = useApi();
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: (input: { mac_address: string }) =>
      request<DataResponse<Device>>("/api/v1/devices", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: (data) => navigate(`/devices/${data.data.id}`),
  });

  return (
    <div className="mx-auto max-w-xl p-6">
      <h2 className="text-xl font-semibold">Add device</h2>
      <form
        className="mt-4 space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          const form = new FormData(e.currentTarget);
          const input = schema.parse({
            mac_address: String(form.get("mac_address") ?? ""),
          });
          mutation.mutate(input);
        }}
      >
        <input
          name="mac_address"
          placeholder="AA:BB:CC:DD:EE:FF"
          className="w-full rounded border p-2"
        />
        <button className="rounded bg-black px-4 py-2 text-white" type="submit">
          Create
        </button>
      </form>
    </div>
  );
}
