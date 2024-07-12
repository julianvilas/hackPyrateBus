# hackPyrateBus

`hackPyrateBus` is a Python library that provides high-level functions to interact with specific integrated circuits using the [Bus Pirate](http://dangerousprototypes.com/docs/Bus_Pirate).
This library takes into account the particularities of the integrated circuits it interacts with.

This project is built on top of [pyBusPirateLite](https://github.com/juhasch/pyBusPirateLite), and we would like to give credit to the original authors and contributors of pyBusPirateLite and pyBusPirate.

_NOTE: the pyBusPirateLite dependency is vendored from https://github.com/julianvilas/pyBusPirateLite/tree/new for convenience, as the original project does not seem to be maintained and it is not available in PyPI neither._
_The `new` branch in that fork contains commits not available in the original upstream, while `master` matches exactly the upstream (as of today)._
_[How to use the module directly](#pybuspiratelite-users)._

## Installation

From PyPI:

```bash
virtualenv venv
source venv/bin/activate

pip install hackPyrateBus
```

From the root of the cloned repo you can install `hackPyrateBus` running:

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

# latest release
url=$(curl --silent "https://api.github.com/repos/julianvilas/hackPyrateBus/releases/latest" | jq -r .assets[0].browser_download_url)
pip install --upgrade $url
```

## Usage

### AT24C128/256 EEPROM

[Datasheet](https://ww1.microchip.com/downloads/en/devicedoc/doc0670.pdf)

Device particularities:

* 16,384/32,768 bytes capacity (`AT24C128`/`AT24C256` respectively) organized as 256/512 64-bytes pages
* Device address range [`0x50`:`0x54`] (default `0x50`), plus a LSB R/W bit (0 write, 1 read)
* Page write mode rolls over when more than 64 bytes are written
* Sequential read with data address auto-increment
* Reading from a concrete data address requires a previous dummy-write

#### Initialize with default values

```python
from hackPyrateBus.AT24CXXX import AT24CXXX
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

### Winbond W25Q64FV Flash Memory

[Datasheet](https://www.winbond.com/resource-files/w25q64fv%20revq%2006142016.pdf)

Device particularities:
* Operates from 2.7V to 3.6V
* 32,768 programmable pages of 256-bytes each
* Up to 256 bytes can be programmed at a time. If the amount of data exceeds the size of the page it rolls over and overwrites the page from the beginning.
* Pages can be erased in groups of 16 (4KB sector erase), groups of 128 (32KB block erase), groups of 256 (64KB block erase) or the entire chip (chip erase)
* Supports SPI, Dual/Quad SPI and QPI
* SPI bus operation Mode 0 (0,0) and 3 (1,1) are supported
* Up to `104MHz` speed supported in Standard SPI for all instructions except `Read data` (`03h`) when operating at 3.0-3.6V
* `50Mhz` Clock frequency for `Read data` when operating at 3.0-3.6V (Bus Pirate maximum SPI speed is `8Mhz`)

_NOTE: the Bus Pirate SPI `write_then_read`'s read operation is slower than_
_expected because for every call it has to return all the data to the UART. As_
_the buffer of the Bus Pirate it is 4096 bytes there is a huge penalty when_
_reading big amounts of the flash, as the Bus Pirate's UART works at 115200 bps._

#### Initialize with default values

```python
from hackPyrateBus.W25Q64FV import W25Q64FV
winbond = W25Q64FV()
winbond.pins = W25Q64FV.PIN_POWER | W25Q64FV.PIN_CS
winbond.config = W25Q64FV.CFG_PUSH_PULL | W25Q64FV.CFG_CLK_EDGE
winbond.speed = '1MHz'
```

Default values:
* Auto-detect and auto-connect to Bus Pirate port
* 115200 bps serial communication speed with Bus Pirate
* 0.5 timeout to ensure full memory can be read/written in a single call
* The Bus Pirate is using the [buzzpirat](https://buzzpirat.com/) compatible firmware. Otherwise set this param as `False`.

### Get memory info

```python
winbond.info()
```

Returns a dictionary containing the following keys:

- `manufacturer`: str
- `device_id`: str
- `unique_id`: str
- `memory_type`: str
- `capacity`: int (in bytes)

#### Read the whole flash memory

```python
img = winbond.read(0x000000, winbond.MAX_WORDS)
with open('flash.img', 'wb') as f:
    f.write(img)

```

* Performs the sequential read using [Bus Pirate Write then read SPI method](http://dangerousprototypes.com/docs/SPI_(binary)#00000100_-_Write_then_read)
* Auto-handles reads of more than 4096 bytes (Bus Pirate buffer size)

#### Overwrite the whole flash memory

```python
with open('flash.img', 'rb') as f:
    winbond.store(0x000000, file.read())

```

* In order to write the the flash, the pages should be previously erased.
The `erase` method is used for that purpose
* Automatically checks if the memory is busy and sets the Write Enable bit

#### Erasing the flash memory:

```python
# erase the whole flash
winbond.erase(winbond.COMMAND_ERASE_CHIP, 0x000000)

# erase a sector (4096 bytes)
winbond.erase(winbond.COMMAND_ERASE_SECTOR, 0x000000)

# erase a 32KB block
winbond.erase(winbond.COMMAND_ERASE_ERASE_32KB, 0x000000)

# erase a 64KB block
winbond.erase(winbond.COMMAND_ERASE_ERASE_64KB, 0x000000)
```

* To calculate the minimum pages required to be erased for writing a content use the `calculate_pages` method

```python
pages = winbond.calculate_pages(0x000000, b'\x00Hello, world!\xff')
```

### pyBusPirateLite users

As previously mentioned `pyBusPirateLite` is vendored in this repo. To directly use that module, just import `vendor.pyBusPirateLite`.

Usage example:

```python
from vendor.pyBusPirateLite.I2C import I2C
```

## Dependencies

This project uses the following open source packages:

- [pyBusPirateLite](https://github.com/juhasch/pyBusPirateLite) (GPLv3)

## License

`hackPyrateBus` is licensed under the GNU General Public License v3 (GPLv3). The full text of the license can be found in the [LICENSE](LICENSE) file.

The pyBusPirateLite project, from which this project is derived, is also licensed under the GPLv3. We would like to thank the authors and contributors of pyBusPirateLite for their work.
