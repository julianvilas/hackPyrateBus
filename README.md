# bphelpers

`bphelpers` is a Python library and command-line interface (CLI) that provides high-level functions to interact with specific integrated circuits using the Bus Pirate.
This library takes into account the particularities of the integrated circuits it interacts with.

This project built on top of [pyBusPirateLite](https://github.com/juhasch/pyBusPirateLite), and we would like to give credit to the original authors and contributors of pyBusPirateLite and pyBusPirate.

## Installation

From the root of the cloned repo you can install `bphelpers` running:

```bash
# from the root of the cloned repo
virtualenv venv
source venv/bin/activate

pip install .
```

Directly From GitHub Releases:

```bash
# from anywhere
virtualenv venv
source venv/bin/activate

pip install --upgrade https://github.com/julianvilas/bphelpers/releases/download/v0.0.1/bphelpers-0.0.1-py3-none-any.whl
```

## Usage

### AT24C128/256

[Datasheet](https://ww1.microchip.com/downloads/en/devicedoc/doc0670.pdf)

Device particularities:

* 16,384/32,768 bytes capacity (`AT24C128`/`AT24C256` respectively) organized as 256/512 64-bytes pages
* Device address range [`0x50`:`0x54`] (default `0x50`), plus a LSB R/W bit (0 write, 1 read)
* Page write mode rolls over when more than 64 bytes are written
* Sequential read with data address auto-increment
* Reading from a concrete data address requires a previous dummy-write

#### Initialize with default values

```python
from bphelpers.AT24CXXX import AT24CXXX
at24c = AT24CXXX()
at24c.speed = '50kHz'
at24c.configure(power=True, pullup=True) # do not enable pullup when using external pullup resistors
```

Default values:
* Auto-detect and auto-connect to Bus Pirate port
* 115200 bps serial communication speed with Bus Pirate
* 1s timeout to ensure full EEPROM can be read/written in a single call
* `256` model
* `0x50` device address

#### Read the first 15 bytes from the EEPROM

```python
at24c.load(0x0000, 15)
```

* Performs dummy-write + sequential read using [Bus Pirate Write then read I2C method](http://dangerousprototypes.com/docs/I2C_(binary)#0x08_-_Write_then_read)
* Auto-handles reads of more than 4096 bytes (Bus Pirate buffer size) 

#### Store data from the 100 position of the EEPROM

```python
at24c.store(100, b'\x00Hello, world!\xff')
```

* Performs page write using [Bus Pirate Write then read I2C method](http://dangerousprototypes.com/docs/I2C_(binary)#0x08_-_Write_then_read)
* Auto-handles writes of more than 64 bytes (page size) to avoid roll-over

#### Reset Bus Pirate

```python
at24c.hw_reset()
```

## Dependencies

This project uses the following open source packages:

- [pyBusPirateLite](https://github.com/juhasch/pyBusPirateLite) (GPLv3)

## License

`bphelpers` is licensed under the GNU General Public License v3 (GPLv3). The full text of the license can be found in the [LICENSE](LICENSE) file.

The pyBusPirateLite project, from which this project is derived, is also licensed under the GPLv3. We would like to thank the authors and contributors of pyBusPirateLite for their work.