from pyBusPirateLite.I2C import I2C

class AT24CXXX(I2C):
    """ Adapted I2C methods for AT24128/256 EEPROMs """

    PAGE_SIZE = 64
    MAX_WORDS_128 = 16384
    MAX_WORDS_256 = 32768

    def __init__(self, portname='', speed=115200, timeout=1.0, connect=True, size=256, device_address=0x50):
        """
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
            Connect to the Bus Pirate
        size : int
            Size of the EEPROM in kbit (128 or 256), default is 256
        device_address : int
            I2C address of the EEPROM without the r/w bit, default is 0x50

        Examples
        --------
        >>> from pyBusPirateLite.AT24CXXX import AT24CXXX
        >>> at24c = AT24CXXX()
        >>> at24c.speed = '50kHz'
        """

        if size not in [128, 256]:
            raise ValueError('Invalid EEPROM size')

        super().__init__(portname, speed, timeout, connect)
        self.i2c_speed = None
        self.size = size
        self.device_address = device_address << 1

    def store(self, addr, data):
        """
        Store data to EEPROM using the write_then_read method

        Parameters
        ----------
        addr : int
            Two byte address in the EEPROM
        data : bytes
            The bytes to write to the EEPROM

        Raises
        ------
        ValueError
            If the address is out of range for the EEPROM size

        Examples
        --------
        >>> at24c.configure(power=True)
        >>> at24c.store(0x0000, b'\x00Hello, world!\xff')
        """

        if self.size == 128:
            if addr > self.MAX_WORDS_128 or len(data) > self.MAX_WORDS_128:
                raise ValueError("Out of range for 128 kbit EEPROM")
        elif self.size == 256:
            if addr > self.MAX_WORDS_256 or len(data) > self.MAX_WORDS_256:
                raise ValueError("Out of range for 256 kbit EEPROM")

        # split the data into PAGE_SIZE byte chunks otherwise the same page is overwritten over and over
        # check the datasheet for the page size 'WRITE OPERATIONS - PAGE WRITE' section
        for i in range(0, len(data), self.PAGE_SIZE):
            header = [self.device_address] + list(addr.to_bytes(2, 'big'))
            r = self.write_then_read(len(header) + len(data[i:i + self.PAGE_SIZE]), 0, header + list(data[i:i + self.PAGE_SIZE]))
            addr += self.PAGE_SIZE

    def load(self, addr, amount):
        """
        Load data from EEPROM using the write_then_read method

        Parameters
        ----------
        addr : int
            Two byte address in the EEPROM
        amount : int
            The number of bytes to read from the EEPROM

        Raises
        ------
        ValueError
            If the address is out of range for the EEPROM size

        Examples
        --------
        >>> at24c.configure(power=True)
        >>> at24c.load(0x0000, 15)
        """

        if self.size == 128:
            if addr > self.MAX_WORDS_128 or amount > self.MAX_WORDS_128:
                raise ValueError("Out of range for 128 kbit EEPROM")
        elif self.size == 256:
            if addr > self.MAX_WORDS_256 or amount > self.MAX_WORDS_256:
                raise ValueError("Out of range for 256 kbit EEPROM")

        # dummy write to set the address pointer
        header = [self.device_address] + list(addr.to_bytes(2, 'big'))
        self.write_then_read(3, 0, header)

        device_address = [self.device_address | 1]
        res = []
        # the bus pirate write_then_read method can only read 4096 bytes at a time
        while amount > 4096:
            # use sequential read mode
            r = self.write_then_read(1, 4096, device_address)
            res.extend(r)
            amount -= 4096
            addr += 4096

        # use sequential read mode
        r = self.write_then_read(1, amount, device_address)
        res.extend(r)

        return bytes(res)
