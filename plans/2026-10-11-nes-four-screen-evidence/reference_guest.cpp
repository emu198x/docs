#include "Shared/SettingTypes.h"
#include "Shared/MemoryType.h"
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <thread>
extern "C" {
void InitDll();
void InitializeEmu(const char*, void*, void*, bool, bool, bool, bool);
void SetNesConfig(NesConfig);
void SetEmulationFlag(int, bool);
bool LoadRom(char*, char*);
uint8_t GetMemoryValue(int, uint32_t);
void Stop();
void Release();
}
static uint8_t read(uint32_t address) {
    return GetMemoryValue(static_cast<int>(MemoryType::NesMemory), address);
}
int main(int argc, char** argv) {
    if(argc != 3) return 2;
    InitDll();
    InitializeEmu(argv[1], nullptr, nullptr, true, true, true, true);
    NesConfig config{};
    config.RamPowerOnState = RamState::AllZeros;
    config.Region = ConsoleRegion::Ntsc;
    SetNesConfig(config);
    SetEmulationFlag(static_cast<int>(EmulationFlags::MaximumSpeed), true);
    char patch[] = "";
    bool ok = LoadRom(argv[2], patch);
    if(ok) {
        for(int poll=0; poll<500 && read(0x04f1)!=0xa5; ++poll)
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        ok = read(0x04f1)==0xa5;
        if(ok) std::printf("%u,%u,%u,%u\n",read(0x0400),read(0x0401),read(0x0402),read(0x0403));
    }
    Stop(); Release();
    if(!ok) std::fprintf(stderr,"guest did not finish\n");
    return ok ? 0 : 1;
}
