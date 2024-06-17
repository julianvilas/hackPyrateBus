from vendor.pyBusPirateLite.SPI import SPI
from vendor.pyBusPirateLite.base import ProtocolError
import binascii

class W25Q64FV(SPI):
    """ Adapted SPI methods for Winbond W25Q64FV flash memory"""

    PAGE_SIZE = 256 # page size in bytes
    MAX_WORDS = PAGE_SIZE * 32768 # max number of words in flash memory

    COMMAND_READ = 0x03
    COMMAND_READ_STATUS_REG_1 = 0x05
    COMMAND_READ_STATUS_REG_2 = 0x35
    COMMAND_WRITE_ENABLE = 0x06
    COMMAND_ERASE_SECTOR = 0x20
    COMMAND_ERASE_32KB = 0x52
    COMMAND_ERASE_64KB = 0xD8
    COMMAND_ERASE_CHIP = 0x60
    COMMAND_MANUFACTURER = 0x90
    COMMAND_UNIQUE_ID = 0x4B
    COMMAND_JEDEC_ID = 0x9F
    COMMAND_PAGE_PROGRAM = 0x02

    def __init__(self, portname='', speed=115200, timeout=0.5, connect=True, buzzpirateFirm=True):
        """
        Provide high-speed access to the Bus Pirate SPI hardware.

        This constructor by default connects to the first Bus Pirate it can
        find. If you don't want that, set connect to False.

        Parameters
        ----------
        portname : str
            Name of comport (/dev/bus_pirate or COM3)
        speed : int
            Communication speed, use default of 115200
        timeout : int
            Timeout in s to wait for reply
        connect : bool
            Connect to the Bus Pirate (default)
        buzzpirateFirm : bool
            Indicate if the firmware is https://buzzpirat.com/ or not. The
            behavior of the write_then_read method is different. The
            SPI.write_then_read method of the BPv3.6 firmware is buggy and only
            returns 0x01 when there is data to read. In buzzpirate firmware that
            is fixed.

        Examples
        --------
        >>> from hackPyrateBus.W25Q64FV import W25Q64FV
        >>> winbond = W25Q64FV()
        >>> winbond.pins = W25Q64FV.PIN_POWER | W25Q64FV.PIN_CS
        >>> winbond.config = W25Q64FV.CFG_PUSH_PULL | W25Q64FV.CFG_CLK_EDGE
        >>> winbond.speed = '1MHz'
        """

        super().__init__(portname, speed, timeout, connect)
        self._config = None
        self._speed = None
        self._cs = None
        self._pins = None

        if not buzzpirateFirm:
            self.write_then_read = self.write_then_read_no_iosuccess

    def read(self, addr, amount):
        """
        Read data from flash memory using the write_then_read method. Currently
        this method is slow as hell because the data is sent to the UART before
        pulling the CS pin high (even though in the documentation it says the CS
        pin is pulled high before sending the data).

        Parameters
        ----------
        addr : int
            Three byte address in the flash memory
        amount : int
            The number of bytes to read from the flash memory

        Raises
        ------
        ValueError
            If the address is out of range for the flash memory size
        ProtocolError
            If the flash memory is busy

        Examples
        --------
        >>> img = winbond.read(0x000000, winbond.MAX_WORDS)
        >>> with open('flash.img', 'wb') as f:
        ...     f.write(img)
        """

        if addr + amount > self.MAX_WORDS:
            raise ValueError("Out of range for flash memory size")

        # check that the flash memory is not busy
        if self.status_registers()[0] & 0x01:
            raise ProtocolError("Flash memory is busy")

        res = []
        # the bus pirate write_then_read method can only read 4096 bytes at a time
        while amount > 4096:
            header = [self.COMMAND_READ] + list(addr.to_bytes(3, 'big'))
            r = self.write_then_read(len(header), 4096, header)
            res.extend(r)
            amount -= 4096
            addr += 4096

        header = [self.COMMAND_READ] + list(addr.to_bytes(3, 'big'))
        r = self.write_then_read(len(header), amount, header)
        res.extend(r)

        return bytes(res)

    def store(self, addr, data):
        """
        Store data to flash memory. The data is split into PAGE_SIZE byte chunks
        and the method takes care of Write Enable.

        Parameters
        ----------
        addr : int
            Three byte address in the flash memory
        data : bytes
            The bytes to write to the flash memory

        Raises
        ------
        ValueError
            If the address is out of range for the flash memory size

        Examples
        --------
        >>> with open('flash.img', 'rb') as f:
        ...     winbond.store(0x000000, file.read())
        """

        if addr + len(data) > self.MAX_WORDS:
            raise ValueError("Out of range for flash memory size")

        # check that the flash memory is not busy
        reg = self.status_registers()
        if reg[0] & 0x01:
            raise ProtocolError("Flash memory is busy")

        # the page size is 256 bytes, so we need to write in chunks of 256 bytes
        data_array = bytearray(data)
        while len(data_array) > 0:
            # enable write
            if reg[0] & 0x02 == 0:
                self.write_enable()

            # ensure we do not overwrite the page boundary
            page_slot = self.PAGE_SIZE - (addr & 0xFF)
            length = min(len(data_array), page_slot)

            header = [self.COMMAND_PAGE_PROGRAM] + list(addr.to_bytes(3, 'big'))
            self.write_then_read(len(header) + length, 0, header + list(data_array[:length]))
            del data_array[:length]
            addr += length

    def calculate_pages(self, addr, data):
        """
        Calculate the number of pages to write to the flash memory.

        Splits the data into PAGE_SIZE byte chunks otherwise the same page is
        overwritten over and over. If a chunk would exceed the page size due to
        the address provided, the remaining bytes are written to the next page.

        Parameters
        ----------
        addr : int
            Three byte address in the flash memory
        data : bytes
            The bytes to write to the flash memory

        Returns
        ----------
        int
            The number of pages to write to the flash memory

        Raises
        ------
        ValueError
            If the address is out of range for the flash memory size

        Examples
        --------
        >>> pages = winbond.calculate_pages(0x000000, b'\x00Hello, world!\xff')
        """

        if addr + len(data) > self.MAX_WORDS:
            raise ValueError("Out of range for flash memory size")

        # calculate the number of pages to write
        pages = len(data) // self.PAGE_SIZE
        if len(data) % self.PAGE_SIZE > 0:
            pages += 1
        if len(data) % self.PAGE_SIZE + addr & 0xFF > self.PAGE_SIZE:
            pages += 1

        return pages

    def erase(self, command, addr):
        """
        Erase the flash memory using the provided command. It takes care of the
        Write Enable.

        Parameters
        ----------
        command : int
            The command to erase the flash memory
        addr : int
            Three byte address in the flash memory. For the chip erase command
            it is ignored.

        Raises
        ------
        ValueError
            If the address is out of range for the flash memory size
        ProtocolError
            If the flash memory is busy

        Examples
        --------
        >>> winbond.erase(winbond.COMMAND_ERASE_CHIP, 0x000000)
        """

        if addr > self.MAX_WORDS and command != self.COMMAND_ERASE_CHIP:
            raise ValueError("Out of range for flash memory size")

        # check that the flash memory is not busy
        reg = self.status_registers()
        if reg[0] & 0x01:
            raise ProtocolError("Flash memory is busy")

        # enable write
        if reg[0] & 0x02 == 0:
            self.write_enable()

        header = [command]
        if command != self.COMMAND_ERASE_CHIP:
            header += list(addr.to_bytes(3, 'big'))
        self.write_then_read(len(header), 0, header)

    def status_registers(self):
        """
        Returns the status registers of the flash memory.

        Returns
        ----------
        bytes
            The status registers of the flash memory

        Examples
        --------
        >>> reg = winbond.read_status_registers()
        """

        # read status register 1
        r = self.write_then_read(1, 1, [self.COMMAND_READ_STATUS_REG_1])
        # read status register 2
        r += self.write_then_read(1, 1, [self.COMMAND_READ_STATUS_REG_2])

        return r

    def write_enable(self):
        """
        Sets the Write Enable Latch (WEL) bit in the Status Register to a 1. The
        WEL bit must be set prior to every Page Program, or Erase operation.

        Examples
        --------
        >>> winbond.write_enable()
        """

        self.write_then_read(1, 0, [self.COMMAND_WRITE_ENABLE])

    def info(self):
        """
        Returns the manufacturer, device ID, unique ID, memory type and capacity
        of the flash memory.

        Returns
        ----------
        dict
            A dictionary containing the following keys:
            - 'manufacturer': str
            - 'device_id': str
            - 'unique_id': str
            - 'memory_type': str
            - 'capacity': int (in bytes)

        Examples
        --------
        >>> winbond.info()
        """

        manufacturer = self.write_then_read(4, 2, [self.COMMAND_MANUFACTURER, 0x00, 0x00, 0x00])
        unique_id = self.write_then_read(5, 8, [self.COMMAND_UNIQUE_ID, 0x00, 0x00, 0x00, 0x00])
        jedec_id = self.write_then_read(1, 3, [self.COMMAND_JEDEC_ID])

        return {
            'manufacturer': hex(manufacturer[0]),
            'device_id': hex(manufacturer[1]),
            'unique_id': '0x' + binascii.hexlify(unique_id).decode(),
            'memory_type': hex(jedec_id[1]),
            'capacity': pow(2, jedec_id[2]),
        }
