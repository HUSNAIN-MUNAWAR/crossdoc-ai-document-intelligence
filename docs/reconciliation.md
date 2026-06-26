# Reconciliation

The reconciliation engine compares invoice, PO, packing list, bill of lading, payment proof and delivery notes for quantity, amount, currency, supplier, buyer, destination, dates, container and duplicate invoice risks.

## Practical notes

- The implementation is honest about optional heavy dependencies.
- Demo data is synthetic and generated locally.
- Core modules are tested through backend pytest tests.
