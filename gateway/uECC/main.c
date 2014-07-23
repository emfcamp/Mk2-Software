#include <iostream>
#include "uECC.h"
#include <string>

int char2int(uint8_t input)
{
    if(input >= '0' && input <= '9')
        return input - '0';
    if(input >= 'A' && input <= 'F')
        return input - 'A' + 10;
    if(input >= 'a' && input <= 'f')
        return input - 'a' + 10;
    throw "Invalid input string";
}

int main(int argc, char *argv[])
{
    if (argc == 1) {
        std::cerr << "Define mode: sign | verify";
        return 1;
    }

    std::string mode(argv[1]);

    // secp160r1
    // ToDo: Move this into file
    uint8_t l_private[uECC_BYTES]     = {0x20, 0x07, 0xae, 0x54, 0x20, 0x07, 0x00, 0x44, 0x00, 0x00, 
                                         0x00, 0x00, 0x2a, 0x33, 0x73, 0x57, 0x27, 0x52, 0x9a, 0xd0};
    uint8_t l_public[uECC_BYTES * 2]  = {0x8a, 0x5a, 0x14, 0xcc, 0xf8, 0x45, 0x21, 0x59, 0x4c, 0xe1, 
                                         0xf8, 0x82, 0x61, 0xfd, 0xa1, 0x87, 0xb5, 0x41, 0x6d, 0xb3,
                                         0xf6, 0xd2, 0x4b, 0xd7, 0x50, 0xc1, 0x76, 0x5c, 0xc2, 0x58, 
                                         0x8f, 0x1d, 0x82, 0x68, 0xec, 0x37, 0x1f, 0xcd, 0xe7, 0x24};

    if (mode.compare("sign") == 0) { 
        uint8_t l_hash[uECC_BYTES];
        uint8_t l_sig[uECC_BYTES*2];

        for (int i=0; i<20; i++) {
            char e1, e2;
            std::cin >> e1;
            std::cin >> e2;
            l_hash[i] = char2int(e1) * 16 + char2int(e2);
        }

        if(uECC_sign(l_private, l_hash, l_sig)) {
            if (uECC_verify(l_public, l_hash, l_sig)) {
                for (int i=0; i<uECC_BYTES; i++) {
                    std::cout << "0123456789abcdef"[l_hash[i]>>4];
                    std::cout << "0123456789abcdef"[l_hash[i]&0xf];
                }
                std::cout << "\n";
                for (int i=0; i<uECC_BYTES*2; i++) {
                    std::cout << "0123456789abcdef"[l_sig[i]>>4];
                    std::cout << "0123456789abcdef"[l_sig[i]&0xf];
                }

                return 0;
            } else {
                std::cerr << "Could not verify created signature";
                return 1;
            }
        } else {
            std::cerr << "Could not create signature";
            return 1;
        }
      
        
    } 

    if (mode.compare("verify") == 0) { 

        uint8_t l_hash[uECC_BYTES];
        uint8_t l_sig[uECC_BYTES*2];

        for (int i=0; i<uECC_BYTES; i++) {
            char e1 = ' ';
            while (!((e1 >= '0' && e1 <= '9') || (e1 >= 'a' && e1 <= 'f') || (e1 >= 'A' && e1 <= 'F'))) {                
                std::cin >> e1;
            }
            char e2;
            std::cin >> e2;
            l_hash[i] = char2int(e1) * 16 + char2int(e2);
        }

        for (int i=0; i<uECC_BYTES * 2; i++) {
            char e1 = ' ';
            while (!((e1 >= '0' && e1 <= '9') || (e1 >= 'a' && e1 <= 'f') || (e1 >= 'A' && e1 <= 'F'))) {                
                std::cin >> e1;
            }
            char e2;
            std::cin >> e2;
            l_sig[i] = char2int(e1) * 16 + char2int(e2);
        }

        if(uECC_verify(l_public, l_hash, l_sig)) {
            std::cout << "OK\n";
            return 0;
        } else {
            std::cout << "Invalid\n";
            return 1;
        }
    } 

    std::cerr << "Onvalid mode: sign | verify";
    return 1;
}