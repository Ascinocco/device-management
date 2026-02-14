import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { useNavigate } from "react-router-dom";

import { useApi, type DataResponse, type Device } from "../lib/api";

const MAC_REGEX = /^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$/;

const schema = z.object({
  mac_address: z.string().regex(MAC_REGEX, "Invalid MAC address format (expected XX:XX:XX:XX:XX:XX)"),
});

export function NewDevicePage() {
  const { request } = useApi();
  const navigate = useNavigate();
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (input: { mac_address: string }) =>
      request<DataResponse<Device>>("/api/v1/devices", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: (data) => navigate(`/devices/${data.data.id}`),
    onError: (err: Error) => {
      setFormError(err.message);
    },
  });

  return (
    <div className="mx-auto max-w-xl p-6">
      <h2 className="text-xl font-semibold">Add device</h2>

      {formError && (
        <p className="mt-2 text-sm text-red-600">{formError}</p>
      )}

      <form
        className="mt-4 space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          setFormError(null);
          const form = new FormData(e.currentTarget);
          try {
            const input = schema.parse({
              mac_address: String(form.get("mac_address") ?? ""),
            });
            mutation.mutate(input);
          } catch (err) {
            if (err instanceof z.ZodError) {
              setFormError(err.errors[0]?.message ?? "Invalid input");
            } else {
              setFormError("Invalid input");
            }
          }
        }}
      >
        <input
          name="mac_address"
          placeholder="AA:BB:CC:DD:EE:FF"
          className="w-full rounded border p-2"
        />
        <button
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
          type="submit"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Creating..." : "Create"}
        </button>
      </form>
    </div>
  );
}
