PAGE_SIZE = 1024 * 8
BYTE_ORDER = "little"
HDR_SIZE = 24
MAX_PAGE_COUNT = 256
META_SIZE = 256

PAGE_TYPE_ROOT = 0 
PAGE_TYPE_INTERNAL = 1
PAGE_TYPE_DATA = 2

class metablock:
    def __init__(self, max_page):
        self.max_page = max_page
    
    def set_max_page(self, max_page):
        self.max_page = max_page
    
    def inc(self):
        self.max_page += 1
        return self.max_page

class blk_driver:
    def __init__(self, dev_id):
        self.id = dev_id
        self.f = open(f"file__{dev_id}", "+wb")
    
    def write_page_buffer(self, id, buffer):
        self.f.seek(id * PAGE_SIZE + META_SIZE)
        self.f.write(buffer)
    
    def write_page(self, page):
        page.update_header_buffer()

        offset = page.id * PAGE_SIZE + META_SIZE
        blen = len(page.buffer)
        self.f.seek(offset)
        self.f.write(page.buffer)
        print(f"writepage: from={offset}, len={blen}")
    
    def read_page_buffer(self, id):
        self.f.seek(id*PAGE_SIZE + META_SIZE)
        print(f"read page: from={id*PAGE_SIZE + META_SIZE}, len={PAGE_SIZE}")
        return self.f.read(PAGE_SIZE)
    
    def read_page(self, id):
        buffer = self.read_page_buffer(id)
        assert len(buffer) == PAGE_SIZE
        return page(*page.parse_header_buffer(buffer))
    
    def init_driver(self):
        self.f.seek(0)
        self.f.write(bytearray(b'\\x00' * (MAX_PAGE_COUNT * PAGE_SIZE + META_SIZE)))
        self.commit_metablock(metablock(0))
    
    def read_metablock(self):
        self.f.seek(PAGE_SIZE)
        meta_buffer = self.f.read(PAGE_SIZE)
        return metablock(int.from_bytes(meta_buffer[:8], byteorder=BYTE_ORDER, signed=False))
    
    def commit_metablock(self, metablock):
        self.f.seek(0)
        print("commit: ", metablock.max_page)
        self.f.write(int.to_bytes(metablock.max_page, byteorder=BYTE_ORDER, signed=False))

class page_allocator:
    def __init__(self, blkdev):
        self.blkdev = blkdev
        self.metablock = blkdev.read_metablock()

    def palloc(self):
        new_page_id = self.metablock.inc() - 1
        return page(new_page_id, -1, -1)

class page:
    def __init__(self, page_id, type, min_key):
        self.id = page_id
        self.min_key = min_key
        self.type = type
        self.buffer = bytearray(b'\\x00' * int((PAGE_SIZE/4)))
    
    def update_header_buffer(self):
        header_buffer = self.ser_header()
        self.buffer[:HDR_SIZE] = header_buffer
    
    def ser_header(self):
        id_buf = self.id.to_bytes(8, byteorder=BYTE_ORDER, signed=False)
        type_buf = self.type.to_bytes(8, byteorder=BYTE_ORDER, signed=False)
        min_key_buf = self.min_key.to_bytes(8, byteorder=BYTE_ORDER, signed=False)
        return id_buf + type_buf + min_key_buf

    @classmethod 
    def parse_header_buffer(cls, buffer):
        id_buf = buffer[:8]        
        type_buf = buffer[8:16]
        min_key_buf = buffer[16:24]

        return int.from_bytes(id_buf, byteorder=BYTE_ORDER), int.from_bytes(type_buf, byteorder=BYTE_ORDER), int.from_bytes(min_key_buf, byteorder=BYTE_ORDER)

def new_data_page(allocator, min_key):
    new_page = allocator.palloc()
    new_page.type = PAGE_TYPE_DATA
    new_page.min_key = min_key
    new_page.update_header_buffer()
    return new_page

def new_root_page(allocator, min_key):
    new_page = allocator.palloc()
    new_page.type = PAGE_TYPE_DATA
    new_page.min_key = min_key
    new_page.update_header_buffer()
    return new_page

class bt_node:
  def __init__(self, min_key, type):
      self.min_key = min_key
      self.type = type
      self.keys = []
      self.slots = []
      self.leaf = False
  
  def insert(self):
      pass
  
def new_bt_root(key):
    pass


if __name__ == "__main__" :
    blk = blk_driver(0)
    alloc = page_allocator(blk)
    print(alloc.metablock.max_page)

    root_page = new_root_page(alloc, 7)
    blk.write_page(root_page)
    #print(root_page.buffer)
    root_page_read = blk.read_page(0)
    print(root_page_read.min_key)

    blk.commit_metablock(alloc.metablock)
