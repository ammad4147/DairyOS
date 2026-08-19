# DairyOS OS Handover Audit

Generated: 2026-08-20T01:07:16.5886731+05:00

| Status | Count |
|---|---:|
| PASS | 35 |
| WARN | 0 |
| FAIL | 0 |
| BLOCKING | 0 |

## Gate

**ELIGIBLE_FOR_NEXT_PHASE**

### P0-ISO-IMG-RAW build - PASS

ISO-IMG-RAW build evidence found.

Evidence: D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\comparison-summary.csv; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\CONSOLIDATED-DIFFERENCE-REPORT.txt; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\REPRODUCTIVE-DATE-AUTHORITY-FOCUS.txt; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__api__farm_planning.py.diff; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__api__farm_planning.py.local; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__api__farm_planning.py.remote; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__data__repositories__repository_factory.py.diff; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__data__repositories__repository_factory.py.local; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__data__repositories__repository_factory.py.remote; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__farm__operations__repositories__adapters__database_breeding_repository.py.diff; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__farm__operations__repositories__adapters__database_breeding_repository.py.local; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\src__dairyos__farm__operations__repositories__adapters__database_breeding_repository.py.remote; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\tools__handover__Invoke-DairyOSAllTests.ps1.diff; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\tools__handover__Invoke-DairyOSAllTests.ps1.local; D:\DairyOS\.dairyo-reconciliation\authority-comparison-20260820-010420\tools__handover__Invoke-DairyOSAllTests.ps1.remote; D:\DairyOS\backups\sprint035\farm_operational_state_current_raw.txt; D:\DairyOS\os\build\build-iso.sh; D:\DairyOS\scripts\HERD-039_Advisory_Engine_Build.ps1; D:\DairyOS\src\dairyos\data\models\__pycache__\drug_withdrawal_reference.cpython-314.pyc; D:\DairyOS\src\dairyos\data\models\drug_withdrawal_reference.py

### P0-Bootloader-EFI - PASS

Bootloader-EFI evidence found.

Evidence: D:\DairyOS\os\boot\grub\grub.cfg; D:\DairyOS\os\pxe\grub.cfg

### P0-Installer-provisioning - PASS

Installer-provisioning evidence found.

Evidence: D:\DairyOS\os\installer\hooks\firstboot.sh; D:\DairyOS\os\installer\hooks\validate.sh; D:\DairyOS\os\installer\install.sh; D:\DairyOS\os\installer\preseed\dairyos.seed; D:\DairyOS\os\installer\rollback.sh

### P0-Partitioning - PASS

Partitioning evidence found.

Evidence: D:\DairyOS\os\partitioning\dairyos.sfdisk

### P0-Kernel - PASS

Kernel evidence found.

Evidence: D:\DairyOS\src\dairyos\intelligence\kernel\__init__.py; D:\DairyOS\src\dairyos\intelligence\kernel\__pycache__\__init__.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\assessment\__init__.py; D:\DairyOS\src\dairyos\intelligence\kernel\assessment\__pycache__\__init__.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\assessment\__pycache__\situation_assessment.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\assessment\situation_assessment.py; D:\DairyOS\src\dairyos\intelligence\kernel\context\__init__.py; D:\DairyOS\src\dairyos\intelligence\kernel\context\__pycache__\__init__.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\context\__pycache__\intelligence_context.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\context\intelligence_context.py; D:\DairyOS\src\dairyos\intelligence\kernel\interface\__init__.py; D:\DairyOS\src\dairyos\intelligence\kernel\interface\__pycache__\__init__.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\interface\__pycache__\intelligence_gateway.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\interface\intelligence_gateway.py; D:\DairyOS\src\dairyos\intelligence\kernel\memory\__init__.py; D:\DairyOS\src\dairyos\intelligence\kernel\memory\__pycache__\__init__.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\memory\__pycache__\intelligence_memory.cpython-314.pyc; D:\DairyOS\src\dairyos\intelligence\kernel\memory\intelligence_memory.py; D:\DairyOS\src\dairyos\intelligence\kernel\models\__init__.py; D:\DairyOS\src\dairyos\intelligence\kernel\models\__pycache__\__init__.cpython-314.pyc

### P0-PXE-network-boot - PASS

PXE-network-boot evidence found.

Evidence: D:\DairyOS\os\pxe\dnsmasq.conf; D:\DairyOS\os\pxe\grub.cfg; D:\DairyOS\os\pxe\ipxe\dairyos.ipxe; D:\DairyOS\os\pxe\mirror\nginx-dairyos.conf; D:\DairyOS\os\pxe\mirror\sync-debian.sh

### P0-Teardown-rollback - PASS

Teardown-rollback evidence found.

Evidence: D:\DairyOS\.dairyo-reconciliation\os-handover-inspection-20260820-010147\remote-install-uninstall-candidates.txt; D:\DairyOS\.dairyo-reconciliation\os-handover-inspection-20260820-010309\remote-install-uninstall-candidates.txt; D:\DairyOS\os\installer\rollback.sh; D:\DairyOS\scripts\install\Uninstall-DairyOS.ps1; D:\DairyOS\src\dairyos\lifecycle\__pycache__\purge.cpython-314.pyc; D:\DairyOS\src\dairyos\lifecycle\purge.py; D:\DairyOS\tests\platform\__pycache__\test_lifecycle_purge.cpython-314.pyc; D:\DairyOS\tests\platform\__pycache__\test_lifecycle_purge.cpython-314-pytest-9.1.1.pyc; D:\DairyOS\tests\platform\test_lifecycle_purge.py

### P0-TOKEN-grub - PASS

Repository text references 'grub'.

Evidence: static source inspection

### P0-TOKEN-systemd - PASS

Repository text references 'systemd'.

Evidence: static source inspection

### P0-TOKEN-kickstart - PASS

Repository text references 'kickstart'.

Evidence: static source inspection

### P0-TOKEN-preseed - PASS

Repository text references 'preseed'.

Evidence: static source inspection

### P0-TOKEN-cloud-init - PASS

Repository text references 'cloud-init'.

Evidence: static source inspection

### P0-TOKEN-pxe - PASS

Repository text references 'pxe'.

Evidence: static source inspection

### P0-TOKEN-ipxe - PASS

Repository text references 'ipxe'.

Evidence: static source inspection

### P0-TOKEN-mkfs - PASS

Repository text references 'mkfs'.

Evidence: static source inspection

### P0-TOKEN-sgdisk - PASS

Repository text references 'sgdisk'.

Evidence: static source inspection

### P0-TOKEN-parted - PASS

Repository text references 'parted'.

Evidence: static source inspection

### P0-TOKEN-efibootmgr - PASS

Repository text references 'efibootmgr'.

Evidence: static source inspection

### P0-TOKEN-wipefs - PASS

Repository text references 'wipefs'.

Evidence: static source inspection

### P0-TOKEN-dracut - PASS

Repository text references 'dracut'.

Evidence: static source inspection

### P0-TOKEN-initramfs - PASS

Repository text references 'initramfs'.

Evidence: static source inspection

### P1-APP-LIFECYCLE - PASS

Application lifecycle test suite exists, but it is not an OS installer test.

Evidence: D:\DairyOS\tests\platform\test_lifecycle_manager.py

### P1-CONTAINER-DEPLOYMENT - PASS

Container deployment definition exists.

Evidence: D:\DairyOS\docker-compose.yml

### P2-HW-rfid - PASS

Static repository references hardware term 'rfid'.

Evidence: source search

### P2-HW-rs485 - PASS

Static repository references hardware term 'rs485'.

Evidence: source search

### P2-HW-serial - PASS

Static repository references hardware term 'serial'.

Evidence: source search

### P2-HW-plc - PASS

Static repository references hardware term 'plc'.

Evidence: source search

### P2-HW-parlor - PASS

Static repository references hardware term 'parlor'.

Evidence: source search

### P2-HW-parlour - PASS

Static repository references hardware term 'parlour'.

Evidence: source search

### P2-HW-touch - PASS

Static repository references hardware term 'touch'.

Evidence: source search

### P2-HW-hid - PASS

Static repository references hardware term 'hid'.

Evidence: source search

### P2-HW-usb - PASS

Static repository references hardware term 'usb'.

Evidence: source search

### P2-HW-ethernet - PASS

Static repository references hardware term 'ethernet'.

Evidence: source search

### P2-HW-modbus - PASS

Static repository references hardware term 'modbus'.

Evidence: source search

### P2-HW-scale - PASS

Static repository references hardware term 'scale'.

Evidence: source search

