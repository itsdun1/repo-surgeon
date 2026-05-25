import { calculateCartTotal } from "../cart";

describe("calculateCartTotal", () => {
  it("totals integer-priced items", () => {
    const total = calculateCartTotal([
      { id: 1, name: "a", price: 10, quantity: 2 },
      { id: 2, name: "b", price: 5, quantity: 1 },
    ]);
    expect(total).toBe(25);
  });

  it("handles decimal-priced items without losing cents (issue #1)", () => {
    const total = calculateCartTotal([
      { id: 1, name: "A", price: 3.99, quantity: 1 },
      { id: 2, name: "B", price: 1.5, quantity: 1 },
    ]);

    expect(total).toBe(5.49);
  });
});
