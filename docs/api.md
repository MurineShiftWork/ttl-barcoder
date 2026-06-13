# API Reference

## BarcodeTTL

Main interface for TTL barcode generation and decoding.

```python
from ttl_barcoder import BarcodeTTL, BarcodeConfig
```

::: ttl_barcoder.BarcodeTTL

---

## BarcodeConfig

Pydantic v2 configuration model. All fields are validated on construction.

```python
from ttl_barcoder import BarcodeConfig, TTLType, TimestampPrecision
```

::: ttl_barcoder.BarcodeConfig

---

## BarcodeDecoder

::: ttl_barcoder.BarcodeDecoder

---

## Generators

::: ttl_barcoder.TTLGenerator

::: ttl_barcoder.TimestampGenerator

::: ttl_barcoder.RandomGenerator

---

## Utilities

::: ttl_barcoder.get_preset

::: ttl_barcoder.create_generator

---

## Enums

::: ttl_barcoder.TTLType

::: ttl_barcoder.TimestampPrecision
