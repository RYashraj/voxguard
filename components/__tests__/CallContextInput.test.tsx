import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import CallContextInput from "@/components/CallContextInput";
import { SimulationContext } from "@/types/risk";

describe("CallContextInput — Data Minimisation & Interaction", () => {
  beforeEach(() => cleanup());

  it("renders selects with default values and privacy disclaimer", () => {
    const defaultCtx: SimulationContext = {
      caller_context: "not_provided",
      transaction_type: "not_provided",
      user_confirmation_required: true,
    };
    const handleChange = vi.fn();

    render(<CallContextInput value={defaultCtx} onChange={handleChange} />);

    expect(screen.getByText("Call Context")).toBeInTheDocument();
    expect(
      screen.getByText("Demo context only. Do not enter personal or banking details.")
    ).toBeInTheDocument();

    const callerSelect = screen.getByLabelText("Caller Status") as HTMLSelectElement;
    expect(callerSelect.value).toBe("not_provided");

    const transactionSelect = screen.getByLabelText("Transaction Type") as HTMLSelectElement;
    expect(transactionSelect.value).toBe("not_provided");

    // No transfer amount input when transaction type is not fund_transfer
    expect(screen.queryByLabelText("Transfer Amount (₹)")).not.toBeInTheDocument();
  });

  it("triggers onChange when caller status or transaction type is selected", () => {
    const initialCtx: SimulationContext = {
      caller_context: "not_provided",
      transaction_type: "not_provided",
      user_confirmation_required: true,
    };
    const handleChange = vi.fn();

    render(<CallContextInput value={initialCtx} onChange={handleChange} />);

    const callerSelect = screen.getByLabelText("Caller Status");
    fireEvent.change(callerSelect, { target: { value: "unknown_contact" } });

    expect(handleChange).toHaveBeenCalledWith({
      caller_context: "unknown_contact",
      transaction_type: "not_provided",
      user_confirmation_required: true,
    });
  });

  it("shows numeric amount input only for fund_transfer and prevents arbitrary free-text fields", () => {
    const fundTransferCtx: SimulationContext = {
      caller_context: "unknown_contact",
      transaction_type: "fund_transfer",
      transaction_amount: 15000,
      user_confirmation_required: true,
    };
    const handleChange = vi.fn();

    render(<CallContextInput value={fundTransferCtx} onChange={handleChange} />);

    const amountInput = screen.getByLabelText("Transfer Amount (₹)") as HTMLInputElement;
    expect(amountInput).toBeInTheDocument();
    expect(amountInput.type).toBe("number");
    expect(amountInput.value).toBe("15000");

    // Ensure no name, account number, or OTP text input exists in the container
    const textInputs = screen.queryAllByRole("textbox");
    expect(textInputs.length).toBe(0);
  });
});
