// ATTENZIONE: QUESTA é UNA COPIA DEL CONTRATTO (non gestiamo la compilazione e deploy da python)

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

contract BatchVerifier {
    struct BatchInfo {
        string merkle_root;
        string cid_merkle_path;
    }

    mapping(uint256 => BatchInfo) public batches;

    /// @notice Salva un nuovo batch. Fallisce se l'id del batch è già presente.
    function salvaBatch(uint256 id, string memory merkle_root, string memory cid_merkle_path) public {
        require(bytes(batches[id].merkle_root).length == 0, "Batch già esistente.");
        batches[id] = BatchInfo(merkle_root, cid_merkle_path);
    }

    /// @notice Restituisce i dati associati a un batch
    function getBatch(uint256 id) public view returns (string memory, string memory) {
        BatchInfo memory info = batches[id];
        return (info.merkle_root, info.cid_merkle_path);
    }
}
