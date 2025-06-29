// ATTENZIONE: QUESTA é UNA COPIA DEL CONTRATTO (non gestiamo la compilazione e deploy da python)

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract BatchVerifier {
    struct BatchInfo {
        string merkleRoot;
        string cidIpfs;
    }

    mapping(uint256 => BatchInfo) public batches;

    /// @notice Salva un nuovo batch. Fallisce se l'id del batch è già presente.
    function salvaBatch(uint256 id, string memory merkleRoot, string memory cidIpfs) public {
        require(bytes(batches[id].merkleRoot).length == 0, "Batch già esistente.");
        batches[id] = BatchInfo(merkleRoot, cidIpfs);
    }

    /// @notice Restituisce i dati associati a un batch
    function getBatch(uint256 id) public view returns (string memory, string memory) {
        BatchInfo memory info = batches[id];
        return (info.merkleRoot, info.cidIpfs);
    }
}
