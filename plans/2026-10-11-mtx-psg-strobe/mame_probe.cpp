#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>
struct sink { std::vector<uint8_t> bytes; void write(uint8_t data) { bytes.push_back(data); } };
struct mtx_state {
    sink *m_sn;
    uint8_t m_sound_latch = 0;
    uint8_t mtx_sound_strobe_r();
    void mtx_sound_latch_w(uint8_t data);
};
#include "mame-handlers.inc"
int main() {
    sink psg;
    mtx_state machine{&psg};
    const bool writes[] = {true,true,false,false,true,false,true,false};
    const uint8_t data[] = {0x85,0xa7,0,0,0x12,0,0x93,0};
    const unsigned expected[] = {0,0,1,2,2,3,3,4};
    std::puts("event,write,input,deliveries,last_delivery");
    for(unsigned i=0;i<8;++i) {
        if(writes[i]) machine.mtx_sound_latch_w(data[i]);
        else (void)machine.mtx_sound_strobe_r();
        assert(psg.bytes.size()==expected[i]);
        std::printf("%u,%u,%u,%zu,%d\n",i,writes[i],data[i],psg.bytes.size(),psg.bytes.empty()?-1:psg.bytes.back());
    }
    assert((psg.bytes==std::vector<uint8_t>{0xa7,0xa7,0x12,0x93}));
}
